# -*- coding: UTF-8 -*-
'''
Created on 2015年3月5日

@author: lixin
'''
from ttypes import UserInfo as UInfo
import urllib,traceback,json,datetime,time,math,re,random,hashlib
from lib.mysql_manager_rw import MysqlConn as mmysql
from lib.redis_manager import m_redis
from user_service.model_score_service import ScoreServiceHandle
from lib.json_manager import CJsonEncoder
from ttypes import InvalidOperation
from base import BaseHandle


class UserServiceHandle(BaseHandle):
    _PREFIX_IOS_OLD = '200'
    _PREFIX_IOS_NEW = '20'
    _PREFIX_ANDROID_OLD = '300'
    _PREFIX_ANDROID_NEW = '30'

    # 滑屏时间间隔配置
    def get_right_catch_time_stamp(self):
        time_stamp = 1200
        return time_stamp
    
    def cacheUpdateUserInfo(self, uid, device_id = "", app_id = 0):
        r = m_redis.get_instance()
        r.delete(m_redis._ZHUAN_USER_LOGIN_NEW_ + str(uid))
        r.delete(m_redis._ZHUAN_USER_SCORE_LIST_GROUP_ + str(uid))
        self.cacheUpdateUserInfoWithApp(uid, app_id)
        if device_id:
            r.delete(m_redis._ZHUAN_USER_ID_BY_DEVICE_ID_ + str(app_id) + "_" + str(device_id))
        
    def cacheUpdateUserInfoWithApp(self, uid, app_id):
        m_redis.get_instance().delete(self._appIdCacheKey(uid, app_id))
        
    def getUserInfoAllUser(self, pnum, ip = "", is_ic = 0, app_id = 0):
        return self.getUserInfo(pnum, ip, is_ic, app_id, all_user = 1)

    def getUserInfo(self, pnum, ip = "", is_ic = 0, app_id = 0, all_user = 0):
        uid = self.getUidByPnum(pnum)
        if not uid:
            return UInfo()
        return self.getUserInfoByUid(uid, ip, is_ic, all_user = all_user, app_id = app_id)
    
    def _get_user_code(self, uid_case = 3):
        m = mmysql()
        uid_code = 0
        ucase = 8
        for i in range(0, 100):
            if isinstance(uid_case, list):
                ucase = uid_case[random.randint(0, len(uid_case) - 1)]
            else:
                ucase = uid_case
            st = 10000000 * ucase
            ed = st + 9999999
            randcode = random.randint(st, ed)
            m.Q('SELECT uid FROM z_user WHERE uid = "%s";' % (randcode))
            rs = m.fetchone()
            if not rs:
                uid_code = randcode
                break
            if i == 100:
                break
        m.close()
        return uid_code
    
    def _get_password(self, password):
        return hashlib.md5(password + 'dianABCDEF12').hexdigest()
    
    def _get_pnum(self, pnum):
        return hashlib.md5(str(pnum) + 'dianABCDE5').hexdigest()
    
    def addUser(self, useraddobj):
        # 生成 uid
        if useraddobj.app_id == 2:
            uid = self._get_user_code(2)
        elif useraddobj.app_id == 1:
            uid = self._get_user_code(6)
        else:
            uid = self._get_user_code() if useraddobj.os_type != "ios" else self._get_user_code(9)
        
        # 处理一下邀请码
        ic = useraddobj.ic
        if not ic:
            ic = 0

        # 免手机号注册，需要分配一个假手机号。安卓为 uid 前 加上 300 或 30，iOS 为 uid 前加上 200 或 20
        pnum = useraddobj.pnum
        if pnum == 0 and useraddobj.os_type == 'android':
            pnum = int(self._PREFIX_ANDROID_OLD + str(uid)) if len(str(uid)) == 8 else int(self._PREFIX_ANDROID_NEW + str(uid))
        elif pnum == 0:
            pnum = int(self._PREFIX_IOS_OLD + str(uid)) if len(str(uid)) == 8 else int(self._PREFIX_IOS_NEW + str(uid))

        # 如果 device_id 已经注册过，就不让注册
        m = mmysql()
        if self.getUidByDeviceId(m.F(useraddobj.device_id), int(useraddobj.app_id)):
            raise InvalidOperation(1, "device_id在这个app_id %s 已经存在" % useraddobj.app_id)
        
        # 开始真正的注册
        try:
            if uid > 0:
                sql = "INSERT INTO z_user(uid, pnum, pnum_md5, password, device_id, imsi, os_type, status, register_ip, ctime, invite_code, channel, from_app, update_time) \
                        VALUES('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', now(), '%s', '%s', '%s', now())" % (uid, int(pnum), self._get_pnum(pnum),
                        self._get_password(useraddobj.pw), m.F(useraddobj.device_id), m.F(useraddobj.imsi), m.F(useraddobj.os_type), 1, m.F(useraddobj.client_ip),
                        int(ic), m.F(useraddobj.channel), int(useraddobj.app_id))
                user_ok = m.Q(sql)
                if user_ok:
                    self.create_user_score_line(uid)
                self.addAppRegister(uid, useraddobj.app_id, useraddobj.device_id, useraddobj.imsi, useraddobj.os_type, useraddobj.channel, useraddobj.client_ip)
            m.close()
            return uid
        except:
            traceback.print_exc()
            m.close()
            return 0
    
    def _appIdCacheKey(self, uid, app_id):
        return m_redis._ZHUAN_APP_ID_ + str(uid) + "_" + str(app_id)
    
    # 首次在某个app登陆，要先注册app
    def addAppRegister(self, uid, app_id, device_id, imsi, os_type, channel, client_ip):
        if not self._validate_param('device_id', device_id):
            return False
        
        m = mmysql()
        try:
            # 新规则 如果device_id 已经被人用了  且uid和你不一样  就不让激活
            # 增加这个规则意义在于 如果z_user表内已经有人用过这个device_id 也是不允许其他人激活的
            sql = "SELECT uid FROM device_id_uid_appid_%s WHERE device_id = '%s';" % (int(app_id), m.F(device_id))                   
            m.Q(sql)
            rs = m.fetchone()
            if rs and rs["uid"] and rs["uid"] != uid:
                return False
            
            sql = "INSERT INTO device_id_uid_appid_%s(device_id, uid, update_time) VALUES('%s', '%s', now())" % (int(app_id), m.F(device_id), int(uid))
            m.Q(sql)
            sql = "INSERT INTO app_register_%s(uid, appid, rtime, device_id, imsi, os_type, channel, register_ip) \
                        VALUES('%s', '%s', now(), '%s', '%s', '%s', '%s', '%s')" % (str(int(uid))[-1], int(uid), int(app_id), m.F(device_id), m.F(imsi) ,m.F(os_type), m.F(channel), m.F(client_ip))
            m.Q(sql)
            self.cacheUpdateUserInfo(int(uid), m.F(device_id), app_id)
        except:
            traceback.print_exc()
            return False
        finally:
            m.close()
            r = m_redis.get_instance()
            r.delete(self._appIdCacheKey(uid, app_id))
        return True
        
    # 注册前先判断否则将失败
    def existAppRegister(self, uid, app_id = 0):
        if not self._validate_param('uid', uid):
            return False
        if not app_id:
            app_id = 0 # 处理一下传上来的 app_id 为 None 的情况
        rs = self._getUserInfoByAppId(uid, app_id)
        if not rs:
            return False
        return True
    
    def getUserPointById(self, uid):
        default_return_rs = {'point': 0, 'subpoint': 0, 'penaltypoint': 0, 'sumpoint': 0, 'vip': 1}
        cache_key =  m_redis._ZHUAN_USER_POINT_ + str(uid)
        r = m_redis.get_instance('ad')
        cache = r.get(cache_key)
        if not cache:
            m = mmysql()
            sql = 'SELECT point, subpoint, penaltypoint, sumpoint FROM user_contribution_%s WHERE uid = %s;' % (str(int(uid))[-1], int(uid))
            m.Q(sql)
            rs = m.fetchone()
            m.close()
            if rs:
                vip = 0
                if rs['sumpoint'] >= 10 and rs['sumpoint'] < 150:
                    vip = 1
                elif rs['sumpoint'] >= 150 and rs['sumpoint'] < 600:
                    vip = 2
                elif rs['sumpoint'] >= 600 and rs['sumpoint'] < 5000:
                    vip = 3
                elif rs['sumpoint'] >= 5000:
                    vip = 4
                rs['vip'] = vip
            r.set(cache_key, json.dumps(rs if rs else default_return_rs, cls = CJsonEncoder), 3600 * 4)
            cache = r.get(cache_key)
        if not cache:
            return default_return_rs
        return json.loads(cache)
    
    def updateUserPoint(self, uid, point, subpoint):
        # 该函数只做加分操作，减分操作是由每天凌晨的脚本跑出来的
        uinfo = self.getUserInfoByUid(uid)
        if not uinfo or uinfo.uid == None:
            return False
        
        stat_date = datetime.datetime.now().strftime("%Y-%m-%d")
        m = mmysql()
        m.Q("INSERT INTO user_contribution_%s VALUES('%s', '%s', %s, 0, 0, `point` + `subpoint` + `penaltypoint`, -100, NOW()) ON DUPLICATE KEY UPDATE \
         stat_date ='%s', `point` = `point` + %d, `sumpoint` = `sumpoint` + %d, utime = now();" % (str(uid)[-1], str(uid), stat_date, int(point), stat_date, int(point), int(point)))

        if int(uinfo.invite_code) and uinfo.invite_code > 0:
            subinfo = self.getUserInfoByUid(uinfo.invite_code)
            if subinfo and subinfo.uid != None:
                m.Q("INSERT INTO user_contribution_%s VALUES('%s', '%s', 50, %s, 0, `point` + `subpoint` + `penaltypoint`, -100, NOW()) ON DUPLICATE KEY UPDATE \
                    stat_date = '%s', subpoint = subpoint + %d, `sumpoint` = `sumpoint` + %d, utime = now();" %
                    (str(uinfo.invite_code)[-1], str(uinfo.invite_code), stat_date, int(subpoint), stat_date, int(subpoint), int(subpoint)))
        m.close()
        # 清除缓存
        cache_key = m_redis._ZHUAN_USER_POINT_ + str(uid)
        r = m_redis.get_instance("ad")
        r.delete(cache_key)
        return True
        
    def _getUserInfoByAppId(self, uid, app_id = 0):
        rkey = self._appIdCacheKey(uid, app_id)
        r = m_redis.get_instance()
        cache = r.get(rkey)
        if not cache:
            m = mmysql()
            sql = "SELECT uid, appid, rtime, device_id, imsi, os_type, channel, register_ip FROM app_register_%s WHERE uid = %s AND appid = %s;" % (str(int(uid))[-1], int(uid), int(app_id))
            m.Q(sql)
            rs = m.fetchone()
            r.set(rkey, json.dumps(rs if rs else {},cls=CJsonEncoder), 86400)
            cache = r.get(rkey)
            m.close()
        if not cache:
            return {}
        return json.loads(cache)

    def getUserInfoByUidAllUser(self, uid, ip = '', is_ic = 0, app_id = 0):
            return self.getUserInfoByUid(uid, ip = '', is_ic = 0, app_id = 0, all_user = 1)
    
    def getUserInfoByUid(self, uid, ip = '', is_ic = 0, app_id = 0, all_user = 0):
        # 从 redis 或数据库里查找用户基本信息
        UserInfo = UInfo()
        u_r_key = m_redis._ZHUAN_USER_LOGIN_NEW_ + str(uid)
        r = m_redis.get_instance()
        user_re = r.get(u_r_key)
        if not user_re:
            m = mmysql()
            if all_user:
                sql_param = '1'
            else:
                sql_param = 'status = 1'
            sql = "SELECT uid, pnum, password, device_id, from_app, channel, ulevel, ctime, status, os_type, imsi, invite_code, register_ip FROM z_user WHERE %s AND uid = '%s';" % (sql_param, int(uid))
            m.Q(sql)
            rs = m.fetchone()
            if rs:
                r.setex(u_r_key, json.dumps(rs, cls = CJsonEncoder), 86400)
            else:
                r.setex(u_r_key, '', 300)
            m.close()
            user_re = r.get(u_r_key)
        if not user_re:
            return UInfo()
        
        # 获取另外一些基本数据并填充到返回值中
        rs = json.loads(user_re)
        if rs: 
            try:
                if self.existAppRegister(uid, app_id):
                    # 覆盖 app 相关信息
                    register_app_info = self._getUserInfoByAppId(uid, app_id)
                    if register_app_info and register_app_info["device_id"]:
                        rs["device_id"] = register_app_info["device_id"]
                        rs["imsi"] = register_app_info["imsi"]
                        rs["os_type"] = register_app_info["os_type"]
                        rs["channel"] = register_app_info["channel"]
                        rs["register_ip"] = register_app_info["register_ip"]
            except:
                traceback.print_exc()
            
            UserInfo.uid = int(rs["uid"])
            UserInfo.mobile = rs["pnum"]
            UserInfo.pword  = rs["password"]
            UserInfo.device_id = rs["device_id"]
            UserInfo.from_app  = rs["from_app"]  
            UserInfo.channel  = rs["channel"]
            UserInfo.ulevel  = rs["ulevel"]
            UserInfo.ctime  = rs["ctime"]
            UserInfo.status  = rs["status"]
            UserInfo.os_type  = rs["os_type"]
            UserInfo.imsi  = rs["imsi"]
            UserInfo.invite_code  = rs["invite_code"]
            UserInfo.register_ip  = rs["register_ip"]
            # 少了总积分和余额

            # 周积分
            week_score = 0
            if week_score:
                UserInfo.week_score = int(week_score)
            else:     
                UserInfo.week_score = 0
            
            # 判断警告用户        
            UserInfo.caution = 1
            if ip:
                caution = self.get_user_caution(UserInfo.uid, ip)
                if caution:
                    UserInfo.caution = 0

            # 如果是畅游就全部小黑屋
            if UserInfo.channel == 'changyou':
                UserInfo.caution = 0
        else:
            return UInfo()
        
        # 返回值填充另外一些数据
        if UserInfo:
            UserInfo.time_stamp = self.get_right_catch_time_stamp()
            #############################递减测试#############################
            # 如果测试不成功可直接删除这段代码
            if UserInfo.ctime and int(str(UserInfo.uid)[-1]) >= 6:
                uctime = int(time.mktime(time.strptime(UserInfo.ctime, '%Y-%m-%d %H:%M:%S')))
                t_cooldown = int(2400 * (1 - math.exp((int(uctime) - time.time()) / 172800)))
                t_cooldown = t_cooldown if t_cooldown > 600 else 600
                UserInfo.time_stamp = self.get_right_catch_time_stamp() if self.get_right_catch_time_stamp() < t_cooldown else t_cooldown
            #############################递减测试#############################
            
            # 积分 余额  这个是后加的
            score_list = self.getUserScoreList(UserInfo.uid)
            if score_list and score_list.has_key("num"):
                UserInfo.total_score = score_list["num"]
                UserInfo.score = score_list["score"]
            
            # 今日积分
            today_user_key = m_redis._ZHUAN_TODAY_USER_SCORE_ + str(datetime.date.today()) + str(uid)       
            today_score = r.get(today_user_key)
            if not today_score:
                today_score = 0
            UserInfo.today_score = int(today_score)
            UserInfo.ic = UserInfo.uid
            UserInfo.ic_content = '{"a":"已收到红包5.xx元，不愧是红包锁屏","b":"红包锁屏送红包，一人5元，速速来领！","c":"旁边女生玩红包锁屏已经赚了50元","d":"在山滴那边海滴那边有一个好软件，它一解锁就送钱，它一解锁就送钱，只要注册就送5元，快来体验红包锁屏！"}'
            UserInfo.ic_url = "http://b.baidumob.com/download.do" 
        return UserInfo
    
    def get_user_caution(self, uid, ip):
        m = mmysql("old_hongbao")
        r = m_redis.get_instance()
        try:
            sql = 'SELECT * FROM z_user_caution WHERE status = 0 AND uid = "%s";' % uid
            m.Q(sql)
            rs = m.fetchone()
            if rs:
                return True
            iplist = []
            ip_cache_list = r.get(m_redis._ZHUAN_USER_BLACK_IP_) or ''
            if ip_cache_list:
                iplist = json.loads(ip_cache_list)
            else:
                sql = 'SELECT black_ip FROM z_ip_black WHERE status = 0;'
                m.Q(sql)
                rs = m.fetchall()
                for row in rs:
                    iplist.append(row["black_ip"])
                r.setex(m_redis._ZHUAN_USER_BLACK_IP_, json.dumps(iplist), 600)

            if iplist:
                for ip_str in iplist:
                    if re.findall(r"%s" % ip_str, ip):
                        return True
        except:
            traceback.print_exc()
            print "ip black is wrong"
        finally:
            m.close()
        return False

    def getUidByDeviceId(self, device_id, app_id = 0):
        r = m_redis.get_instance()
        if app_id == None:
            raise InvalidOperation(1, "app_id is None.")
        
        device_id_key = m_redis._ZHUAN_USER_ID_BY_DEVICE_ID_ + str(app_id) + "_" + str(device_id)
        uid = r.get(device_id_key)
        if not uid:
            m = mmysql()
            sql = "SELECT uid FROM device_id_uid_appid_%s WHERE device_id = '%s';" % (int(app_id), m.F(device_id))                   
            m.Q(sql)
            rs = m.fetchone()
            if not rs:
                sql = 'SELECT uid FROM z_user WHERE device_id = "%s"' % m.F(device_id)
                m.Q(sql)
                rs = m.fetchone()
            if rs:
                uid = rs["uid"]
                r.setex(device_id_key, uid, 800)
            else:
                m.close()
                return 0
            m.close()

        return int(uid)
    
    def getUidByPnum(self, pnum):
        r = m_redis.get_instance()
        pnum = str(pnum)
        uid = r.get(m_redis._ZHUAN_USER_ID_BY_PNUM_ + str(pnum))
        if not uid:
            uid = 0
            m = mmysql()
            sql = 'SELECT uid FROM z_user WHERE pnum = "%s";' % m.F(pnum)
            m.Q(sql)
            rs = m.fetchone()
            if rs:
                uid = rs["uid"]
                r.setex(m_redis._ZHUAN_USER_ID_BY_PNUM_ + str(pnum), uid, 86400)
            else:
                m.close()
                return 0
            m.close()
        
        return int(uid)
    
    def getUserCaution(self, uid, ip):
        return self.get_user_caution(uid, ip)
    
    def getUserCautionByIp(self, ip):
        m = mmysql("old_hongbao")
        r = m_redis.get_instance()
        try:
            iplist = []
            ip_cache_list = r.get(m_redis._ZHUAN_USER_BLACK_IP_) or ""
            if ip_cache_list:
                iplist = json.loads(ip_cache_list)
            else:
                sql = 'SELECT black_ip FROM z_ip_black WHERE status = 0;'
                m.Q(sql)
                rs = m.fetchall()
                for row in rs:
                    iplist.append(row["black_ip"])
                r.setex(m_redis._ZHUAN_USER_BLACK_IP_, json.dumps(iplist), 600)
        
            if iplist:
                for ip_str in iplist:
                    if re.findall(r"%s" % ip_str, ip):
                        return True
        except:
            traceback.print_exc()
            print "ip black is wrong"
        finally:
            m.close()
        return False
    
    def existUser(self, uid):
        r = m_redis.get_instance()
        u_r_key = m_redis._ZHUAN_USER_LOGIN_NEW_ + str(uid)
        user_re = r.get(u_r_key)
        if user_re:
            return True
        
        m = mmysql()
        sql = "SELECT 'x' FROM z_user WHERE uid = '%s';" % int(uid)
        m.Q(sql)
        rs = m.fetchone()
        if rs and rs["x"]:
            m.close()
            return True
        m.close()
        return False
    
    def validateUser(self, pnum, password, ip, device_id = "", uid = 0, app_id = 0):
        user_info = self.getUserInfo(pnum, ip, 0, app_id, 0)
        if user_info:
            if password == user_info.pword:
                if device_id and user_info.device_id != device_id:
                    return False
                if uid and user_info.uid != uid:
                    return False
                return True
        return False
    
    def userScoreMaxCheck(self, uid, score):
        if not score:
            return False
        today = str(datetime.date.today())
        today_score_key = m_redis._ZHUAN_USER_SCORE_MAX_ + today + "_" + str(uid)
        r = m_redis.get_instance()
        today_score = r.get(today_score_key)
        return_rs = False
        if today_score and int(today_score) > 50:
            return_rs = True
        r.incr(today_score_key, int(score))
        r.expire(today_score_key, 86400 * 2)
        return return_rs

    def updateUserDeviceId(self, uid, old_device_id, new_device_id, app_id = 0):
        uid = int(uid)
        old_device_id = mmysql.F(old_device_id)
        new_device_id = mmysql.F(new_device_id)
        m = mmysql()
        sql = "UPDATE z_user SET device_id = '%s', update_time = NOW() WHERE status = 1 AND device_id = '%s' AND uid = %s AND from_app = %s;" % (new_device_id, old_device_id, uid, int(app_id))
        m.Q(sql)
        sql = "UPDATE app_register_%s SET device_id = '%s' WHERE uid = %s AND device_id = '%s' AND appid = %s;" % (str(uid)[-1], new_device_id, uid, old_device_id, int(app_id))
        m.Q(sql)
        sql = "UPDATE device_id_uid_appid_%s SET device_id = '%s' WHERE uid = %s AND device_id = '%s';" % (int(app_id), new_device_id, uid, old_device_id)
        m.Q(sql)
        m.close()
        self.cacheUpdateUserInfo(uid, old_device_id,app_id)
        return True
    
    def updateUserPassword(self, password, uid, pnum):
        password = self._get_password(password)
        m = mmysql()
        sql = "UPDATE z_user SET password = '%s', update_time = NOW() WHERE uid = %s AND pnum = '%s';" % (password, uid, pnum)
        m.Q(sql)
        m.close()
        self.cacheUpdateUserInfo(uid)
        return True
    
    def getInviteMember(self, uid):
        r = m_redis.get_instance("ad")
        invite_key = m_redis._ZHUAN_INVITE_MEMBER_ + str(uid) 
        num = r.get(invite_key)
        if not num:
            m = mmysql()
            sql = "SELECT COUNT(uid) AS num FROM z_user WHERE invite_code = '%s';" % (int(uid))
            m.Q(sql)
            rs = m.fetchone()
            if rs:
                num = rs["num"]
                r.setex(invite_key,rs["num"],800)
            else:
                m.close()
                return 0
            m.close()
        return int(num)
    
    def isTestUser(self, pnum):
        m = mmysql()
        try:
            sql = 'SELECT who FROM test_user_list WHERE pnum = %s;' % pnum
            m.Q(sql)
            rs = m.fetchone()
            if rs:
                return True
        except:
            traceback().print_exc()
        finally:
            m.close()
        
        return False
            
    def delUser(self, pnum):
        print pnum
        if not re.findall("^[0-9]{11}$", str(pnum)):
            return False
        
        uinfo = self.getUserInfo(pnum)
        if uinfo and uinfo.uid:
            if not self.isTestUser(pnum):
                return False

            uid = str(uinfo.uid)
            m = mmysql("old_hongbao")
            sql = "DELETE FROM z_verify_log WHERE mobile = '%s';" % str(uinfo.mobile)
            m.Q(sql)
            sql = "DELETE FROM z_push_ios WHERE uid = %s;" % str(uid)
            m.Q(sql)
            sql = 'DELETE FROM z_user WHERE uid = %s;' % (uid)
            m.Q(sql)
            sql = 'DELETE FROM z_user WHERE pnum = "%s";' % (pnum)
            m.Q(sql)
            m.close()
            newdatadb = mmysql(self.witchDb(uid))
            sql = 'DELETE FROM z_user_score_%s WHERE uid = %s;' % (str(uid)[-1], uid)
            newdatadb.Q(sql)
            sql = 'DELETE FROM z_score_log_%s WHERE uid = %s;' % (str(uid)[-1], uid)
            newdatadb.Q(sql)
            newdatadb.close()
            md = mmysql("old_hongbao_data")
            sql = 'DELETE FROM zhuan_yxpopo_data.z_quest_user_%s WHERE uid = %s;' % (uid[-2:], uid)
            md.Q(sql)
            md.close()
            m = mmysql()
            sql = 'DELETE FROM z_user WHERE uid = %s;' % uid
            m.Q(sql)
            sql = 'DELETE FROM device_id_uid_appid_0 WHERE uid = %s;' % uid
            m.Q(sql)
            sql = 'DELETE FROM device_id_uid_appid_1 WHERE uid = %s;' % uid
            m.Q(sql)
            sql = 'DELETE FROM device_id_uid_appid_2 WHERE uid = %s;' % uid
            m.Q(sql)
            sql = 'DELETE FROM device_id_uid_appid_3 WHERE uid = %s;' % uid
            m.Q(sql)
            sql = 'DELETE FROM device_id_uid_appid_4 WHERE uid = %s;' % uid
            m.Q(sql)
            sql = 'DELETE FROM device_id_uid_appid_5 WHERE uid = %s;' % uid
            m.Q(sql)
            sql = 'DELETE FROM z_user_info_ex WHERE uid = %s;' % uid
            m.Q(sql)
            sql = 'DELETE FROM app_register_%s WHERE uid = %s;' % (str(uid)[-1], uid)
            m.Q(sql) 
            m.close()
            self.cacheUpdateUserInfo(uid,uinfo.device_id, 0)
            self.cacheUpdateUserInfo(uid,uinfo.device_id, 1)
            self.cacheUpdateUserInfo(uid,uinfo.device_id, 2)
            self.cacheUpdateUserInfo(uid,uinfo.device_id, 3)
            self.cacheUpdateUserInfo(uid,uinfo.device_id, 4)
            self.cacheUpdateUserInfo(uid,uinfo.device_id, 5)
            r = m_redis.get_instance()
            r.delete('_ZHUAN_U_L' + str(uid))
            r.delete('_ZHUAN_U_P' + str(uinfo.mobile)) 
            r.delete('_ZHUAN_U_I_B_D_I' + str(uinfo.device_id))
            r.delete('_ZHUAN_U_S_A_L_' + str(uid))
            self.cacheUpdateUserInfoWithApp(uid, 0)
            self.cacheUpdateUserInfoWithApp(uid, 1)
            self.cacheUpdateUserInfoWithApp(uid, 2)
            self.cacheUpdateUserInfoWithApp(uid, 3)
            self.cacheUpdateUserInfoWithApp(uid, 4)
            self.cacheUpdateUserInfoWithApp(uid, 5)
            # 绑定次数key
            bkey = "_ZHUAN_%s%s_%s" % ("ValidateBindNewPhone", "bindtime" + str(uid), str(datetime.date.today())[:7])
            r.delete(bkey)
            return True
        else:
            return False

    def delUserEx(self, pnum):
        print pnum
        if not re.findall("^[0-9]{11}$", str(pnum)):
            return False
        
        uinfo = self.getUserInfo(pnum)
        if uinfo and uinfo.uid:
            if not self.isTestUser(pnum):
                return False

            uid = str(uinfo.uid)
            print uid
            m = mmysql("old_hongbao")
            strDate = time.strftime('%Y%m%d%H%M%S')[2:]
            sql = "UPDATE z_verify_log SET device_id = concat(`device_id`, '-%s'), mobile = %s WHERE mobile = '%s';" % (strDate, strDate, uinfo.mobile)
            m.Q(sql)
            sql = "UPDATE z_push_ios SET device_id = concat(`device_id`, '-%s') WHERE uid = '%s';" % (strDate, uid)
            m.Q(sql)
            sql = "UPDATE z_user SET device_id = concat(`device_id`, '-%s'), pnum = '%s' WHERE uid = %s;" % (strDate, strDate, uid)
            m.Q(sql)
            m.close()
            newdatadb = mmysql(self.witchDb(uid))
            sql = "UPDATE z_score_log_%s SET device_id = concat(`device_id`, '-%s') WHERE uid = '%s';" % (str(uid)[-1], strDate, uid);
            newdatadb.Q(sql)
            newdatadb.close()
            m = mmysql()
            sql = "UPDATE z_user SET device_id = concat(`device_id`, '-%s'), pnum = %s WHERE uid = %s;" % (strDate, strDate, uid)
            m.Q(sql)
            sql = "UPDATE device_id_uid_appid_0 SET device_id = concat(`device_id`, '-%s') WHERE uid = %s;" % (strDate, uid)
            m.Q(sql)
            sql = "UPDATE device_id_uid_appid_1 SET device_id = concat(`device_id`, '-%s') WHERE uid = %s;" % (strDate, uid)
            m.Q(sql)
            sql = "UPDATE device_id_uid_appid_2 SET device_id = concat(`device_id`, '-%s') WHERE uid = %s;" % (strDate, uid)
            m.Q(sql)
            sql = "UPDATE device_id_uid_appid_3 SET device_id = concat(`device_id`, '-%s') WHERE uid = %s;" % (strDate, uid)
            m.Q(sql)
            sql = "UPDATE device_id_uid_appid_4 SET device_id = concat(`device_id`, '-%s') WHERE uid = %s;" % (strDate, uid)
            m.Q(sql)
            sql = "UPDATE device_id_uid_appid_5 SET device_id = concat(`device_id`, '-%s') WHERE uid = %s;" % (strDate, uid)
            m.Q(sql)
            sql = "UPDATE app_register_%s SET device_id = concat(`device_id`, '-%s') WHERE uid = %s;" % (str(uid)[-1], strDate, uid)
            m.Q(sql)
            m.close()
            self.cacheUpdateUserInfo(uid,uinfo.device_id, 0)
            self.cacheUpdateUserInfo(uid,uinfo.device_id, 1)
            self.cacheUpdateUserInfo(uid,uinfo.device_id, 2)
            self.cacheUpdateUserInfo(uid,uinfo.device_id, 3)
            self.cacheUpdateUserInfo(uid,uinfo.device_id, 4)
            self.cacheUpdateUserInfo(uid,uinfo.device_id, 5)
            r = m_redis.get_instance()
            r.delete('_ZHUAN_U_L' + str(uid))
            r.delete('_ZHUAN_U_P' + str(uinfo.mobile)) 
            r.delete('_ZHUAN_U_I_B_D_I' + str(uinfo.device_id))
            r.delete('_ZHUAN_U_S_A_L_' + str(uid))
            self.cacheUpdateUserInfoWithApp(uid, 0)
            self.cacheUpdateUserInfoWithApp(uid, 1)
            self.cacheUpdateUserInfoWithApp(uid, 2)
            self.cacheUpdateUserInfoWithApp(uid, 3)
            self.cacheUpdateUserInfoWithApp(uid, 4)
            self.cacheUpdateUserInfoWithApp(uid, 5)
            # 绑定次数key
            bkey = "_ZHUAN_%s%s_%s" % ("ValidateBindNewPhone", "bindtime" + str(uid), str(datetime.date.today())[:7])
            r.delete(bkey)
            return True
        else:
            return False
    
    def updateUserStatus(self, uid, status):
        if status not in [0, 1, 2]:
            return False
        m = mmysql()
        sql = "UPDATE z_user SET status = %s, update_time = NOW() WHERE uid = %s" % (status, uid)
        m.Q(sql)
        m.close()
        self.cacheUpdateUserInfo(uid)
        return True

    def updateUserMobile(self, uid, pnum):
        m = mmysql()
        try:
            sql = 'SELECT pnum FROM z_user WHERE uid = %s;' % uid
            m.Q(sql) 
            rs = m.fetchone()
            if not rs:
                return 'uid 对应的用户不存在'

            # 只有免注册的手机号才允许修改，开头是'200', '20', '300', '30'
            mobile = str(rs['pnum'])
            if mobile[:3] != self._PREFIX_ANDROID_OLD and mobile[:2] != self._PREFIX_ANDROID_NEW and mobile[:3] != self._PREFIX_IOS_OLD and mobile[:2] != self._PREFIX_IOS_NEW:
                return '不允许修改手机号'

            # 检查手机号是否已经存在
            sql = 'SELECT * FROM z_user WHERE pnum = %s;' % pnum
            m.Q(sql)
            if m.fetchone():
                return '新手机号已经被其他账号绑定'

            # 可以更改了
            sql = 'UPDATE z_user SET pnum = %s, pnum_md5 = "%s", update_time = NOW() WHERE uid = %s;' % (pnum, self._get_pnum(pnum), uid)
            m.Q(sql)
            self.cacheUpdateUserInfo(uid)
            return ''
        except:
            traceback().print_exc()
        finally:
            m.close()
        
        return '服务器错误'

    def updateUserMobileForAdmin(self, uid, old_mobile, new_mobile):
        m = mmysql()
        try:
            sql = 'SELECT pnum FROM z_user WHERE uid = %s AND pnum = %s;' % (uid, old_mobile)
            m.Q(sql) 
            rs = m.fetchone()
            if not rs:
                return 'uid 和 old_mobile 对应的用户不存在'

            # 检查新手机号是否已经存在
            sql = 'SELECT * FROM z_user WHERE pnum = %s;' % new_mobile
            m.Q(sql)
            if m.fetchone():
                return '新手机号已经被其他账号绑定'

            # 走到这里说明是 web 版的手机号，可以更改了
            sql = 'UPDATE z_user SET pnum = %s, pnum_md5 = "%s", update_time = NOW() WHERE uid = %s;' % (new_mobile, self._get_pnum(new_mobile), uid)
            m.Q(sql)
            self.cacheUpdateUserInfo(uid)
            return ''
        except:
            traceback().print_exc()
        finally:
            m.close()
        
        return '服务器错误'

