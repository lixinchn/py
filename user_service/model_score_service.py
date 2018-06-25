# -*- coding: UTF-8 -*-
'''
Created on 2015年3月5日

@author: lixin
'''


from ttypes import *
import urllib,traceback,json,datetime,time,math,re
from lib.mysql_manager_rw import MysqlConn as mmysql
from lib.redis_manager import m_redis

'''
$data = array(
                'device_id' => $device_id,
                'snuid' => $snuid, 可以下发id？
                'app_id' => $app_id,
                'currency' => $rmb, 积分价格（分）
                'app_ratio' => $app_ratio,
                'trade_type' => $trade_type,  广告类型
                'time_stamp' => $time_stamp,
                'token' => $token,
                'return_type' => "simple",
                'ad_name' => $ad_name,
                'pack_name' => $pack_name,  广告标识用order_id
                'order_id'=>md5($device_id.$pack_name.$trade_type.(isset($options['task_id']) ? $options['task_id'] : '') )
            );
            
            /receive.do?device_id=863151020303571&snuid=&app_id=c81bc556d5dc52b854f591320d4c951b&currency=60&app_ratio=1&trade_type=1&time_stamp=1408006179&token=469a1116acd9556180cdc221870d48f7&return_type=simple&ad_name=%E5%92%8C%E8%A7%86%E7%95%8C&pack_name=cn.cmvideo.isj&order_id=e7bc696070bf6423b6b6f65a03caf250


    action type :
        0 是广告墙来源
        1 是划屏加分
        2 是注册加分
'''


class ScoreServiceHandle():
    #增加action的话下面几个内容都要加
    _SCORE_TYPE_NAME = {0: u"应用下载",
                        1: u"划屏加分",
                        2: u"邀请好友",
                        3: u"其他收益",
                        4: u"任务收益",
                        5: u"活动收益",
                        6: u"余额减少",
                        7: u"兑换退款",
                        8: u"分享wifi",
                        9: u"绑卡广告加分",
                        10: u"广告墙2.0加分",
                        11: u"徒弟或徒孙等产生的加分"}
    
    _SCORE_TYPE_DB_NAME = { 0: "score_ad",
                            1: "score_right_catch",
                            2: "score_register",
                            3: "score_other",
                            4: "score_task",
                            5: "score_active",
                            8: "score_field_1",
                            9: "score_field_2",
                            10: "score_field_3",
                            11: "score_field_4"}


    def __init__(self):
        pass

    def witchDb(self, uid):
        return "score_%s" % str(uid)[-2]
    
    def witchScoreTable(self, uid):
        return "z_user_score_%s" % str(uid)[-1]
    
    def witchScoreLogTable(self, uid):
        return "z_score_log_%s" % str(uid)[-1]
    
    def create_user_score_line(self, uid):
        m = mmysql(self.witchDb(uid))
        sql = "INSERT INTO z_user_score_%s(uid, score, update_time) VALUES('%s', 0, now())" % (str(uid)[-1], uid)
        m.Q(sql)
        m.close()
        return True
        
    def addScore(self, ScoreAddObj):
        try:
            currency = int(ScoreAddObj.currency)
        except:
            return False
        
        try:
            # uid 不能为空，不能为0，且必须存在
            uid = int(ScoreAddObj.uid)
            if not uid:
                return False
        except:
            return False
        
        try:
            # uid 不能为空，不能为0，且必须存在
            app_id = int(ScoreAddObj.app_id)
            if not app_id:
                app_id = 0
        except:
            return False

        server_ip = ""
        try:
            #uid 不能为空 不能为0 且必须存在
            server_ip = self.remoteAddress
        except:
            pass
        
        # 退款和兑换只加减余额和记录
        score_sql_str = ''
        if ScoreAddObj.action_type not in [6, 7]:
            # 更新主表的加分类别，如果加分类别不存在则主表更新不会成功，因此出错返回
            try:
                score_str = self._SCORE_TYPE_DB_NAME[ScoreAddObj.action_type]
                if not score_str:
                    return False
                score_sql_str = ", %s = %s + %s" % (score_str, score_str, currency)
            except:
                return False
            
        m = mmysql(self.witchDb(uid))
        balance = 0
        try:
            
            sql = "SELECT uid, score FROM %s WHERE uid = '%s';" % (self.witchScoreTable(uid), int(uid))
            m.Q(sql)
            rs = m.fetchone()
            if not rs:
                balance = currency
                if self.existUser(uid):
                    self.create_user_score_line(uid)
            else:
                balance = int(rs["score"]) + currency

            # 如果是扣款，检查一下金额是否足够
            if currency < 0 and balance < 0:
                m.close()
                return False
            
            # log表规则是取uid倒数第2位分库 最后1位分表 共100个表（包括0）
            sql = "UPDATE %s SET score = score + %s, update_time = now() %s WHERE uid = '%s';" % (self.witchScoreTable(uid), currency, score_sql_str, int(uid))
            m.Q(sql)
            # 后面不能放东西
        except:
            traceback.print_exc()
            m.close()
            return False
        
        # 如果今天有缓存，更新积分退款和减余额全部更新缓存
        r = m_redis.get_instance()
        r.delete(self._scoreListKey(uid))
                
        # log
        try:
            # log表规则是取uid倒数第2位分库 最后1位分表 共100个表（包括0）
            time_stamp = ScoreAddObj.time_stamp
            if not ScoreAddObj.time_stamp:
                    time_stamp = 123457
            if not ScoreAddObj.order_id:
                ScoreAddObj.order_id = ''
            if not ScoreAddObj.ad_name:
                ScoreAddObj.ad_name = ''
            if not ScoreAddObj.client_ip:
                ScoreAddObj.client_ip = ''
            sql = "INSERT INTO %s(uid, device_id, score, ad_id, ad_type, ad_name, ctime, order_id, time_stamp, action_type, ip, balance, app_from, server_ip) \
                        values('%s', '%s', %s, '%s', '%s', '%s', now(), '%s', '%s', %s, '%s', '%s', '%s', '%s')" % \
                        (self.witchScoreLogTable(uid), int(uid), m.F(ScoreAddObj.device_id), currency, m.F(ScoreAddObj.pack_name), int(ScoreAddObj.trade_type),
                        m.F(ScoreAddObj.ad_name), m.F(ScoreAddObj.order_id), int(time_stamp), ScoreAddObj.action_type, m.F(ScoreAddObj.client_ip),
                        balance, app_id, server_ip)
            m.Q(sql)
        except:
            traceback.print_exc()
        finally:
            m.close()
            
        # 增加一个记录今天的积分的缓存 采用累计的方式
        # 替换前需要getUserInfoByUid中修改今日收益
        try:
            if ScoreAddObj.action_type not in [6, 7]:
                r = m_redis.get_instance()
                today_user_key = m_redis._ZHUAN_TODAY_USER_SCORE_ + str(datetime.date.today()) + str(uid)
                r.incr(today_user_key, int(currency))
                r.expire(today_user_key, 86400 * 2)
        except:
            traceback.print_exc()
            print "today is wrong"
        
        # 下面这个以后会替代今日收益
        try:
            if ScoreAddObj.action_type not in [6, 7]:
                r = m_redis.get_instance()
                today_user_key = m_redis._ZHUAN_TODAY_USER_SCORE_NEW_ + str(datetime.date.today()) + str(uid)
                r.hincrby(today_user_key, "today_score", int(currency))
                r.hincrby(today_user_key, ScoreAddObj.action_type, int(currency))
                if ScoreAddObj.action_type in [0, 2]:
                    r.hincrby(today_user_key, "%s_num" % ScoreAddObj.action_type)
                r.expire(today_user_key, 86400 * 2)
        except:
            traceback.print_exc()
            print "today is wrong"
            
        # 删除一下这个月用户下载广告次数的缓存
        r.delete(m_redis._ZHUAN_USER_SCORE_TIME_THIS_MONTH_ + str(uid))

        # 处理一下小额兑换
        self._addScoreSmallExchangeWork(str(uid), ScoreAddObj, currency)

        return True     
    
    def getUserTodayScoreList(self, uid, is_yesteday = True):
        if is_yesteday:
            str_day = str(datetime.date.today() - datetime.timedelta(days = 1))
        else:
            str_day = str(datetime.date.today())
        today_user_key = m_redis._ZHUAN_TODAY_USER_SCORE_NEW_ + str_day + str(uid)
        r = m_redis.get_instance()
        alllist = r.hgetall(today_user_key)

        for key in alllist.keys():
            alllist[key] = int(alllist[key])
        return alllist    
    
    def _scoreListKey(self,uid):
        return m_redis._ZHUAN_USER_SCORE_ALL_LIST_ + str(uid)
    
    def _getUserScoreList(self, uid):
        r = m_redis.get_instance()
        list = r.hgetall(self._scoreListKey(uid))
        if not list:
            m = mmysql(self.witchDb(uid))
            sql = 'SELECT uid, score, update_time, score_ad, score_right_catch, score_register, score_other, score_task, score_active, \
                    score_field_1 AS wifi_share, score_field_2 AS bind_bank_card, score_field_3 AS ad_wall_20, score_field_4 AS score_offspring, \
                    score_ad + score_right_catch + score_register + score_other + score_task + score_active + score_field_1 + score_field_2 + score_field_3 + score_field_4 as num \
                    FROM %s WHERE uid = "%s";' % (self.witchScoreTable(uid), int(uid))
            m.Q(sql)
            rs = m.fetchone()
            if not rs:
                return {}
            rs['update_time'] = int(time.mktime(rs['update_time'].timetuple()))
            m.close()
            r.hmset(self._scoreListKey(uid), rs)
            r.expire(self._scoreListKey(uid), 86400)
            list = r.hgetall(self._scoreListKey(uid))
        
        for key in list.keys():
            list[key] = int(list[key])
        return list
    
    def getUserBalance(self, uid):
        rs = None
        list_str = self._getUserScoreList(uid)

        if list_str:
            return int(list_str["score"])
        else:
            return 0
        
    def getUserScoreList(self, uid):
        if not self._validate_param('uid', uid):
            return {}
        rs = self._getUserScoreList(uid)
        if not rs:
            return {}
        return rs
        
    def getUserThisMonthScoreTime(self, uid, action_type = 0):
        r = m_redis.get_instance()
        scoreTimeMonthly = r.get(m_redis._ZHUAN_USER_SCORE_TIME_THIS_MONTH_ + str(uid))
        if scoreTimeMonthly == None:
            today = datetime.date.today()
            firstDay = datetime.date(day = 1, month = today.month, year = today.year)
            firstDay = firstDay.strftime('%Y-%m-%d %H:%M:%S')
            
            m = mmysql(self.witchDb(uid))
            sql = 'SELECT count(*) as time FROM %s WHERE uid = %s AND action_type = %s AND ctime >= "%s";' % (self.witchScoreLogTable(uid), int(uid), int(action_type), firstDay)
            m.Q(sql)
            result = m.fetchone()
            scoreTimeMonthly = result['time']
            r.setex(m_redis._ZHUAN_USER_SCORE_TIME_THIS_MONTH_ + str(uid), scoreTimeMonthly, 60 * 60)

        return int(scoreTimeMonthly)

    def checkUserAdOrInviteInSevenDays(self, uid, sdate):
        m = mmysql(self.witchDb(uid))
        sql = 'SELECT count(*) AS total FROM %s WHERE (action_type = %s OR action_type = %s) AND uid = %s AND ctime >= date_add("%s", interval -6 day) AND ctime <= date_add("%s", interval 1 day)' % \
                (self.witchScoreLogTable(uid), Scoretype._ACTION_TYPE_AD, Scoretype._ACTION_TYPE_REGISTER, uid, sdate, sdate)
        m.Q(sql)
        result = m.fetchone()
        return True if result['total'] > 0 else False

    def resumeUserScoreForExchange(self, uid, score):
        if not self._validate_param('uid', uid):
            return False

        m = mmysql(self.witchDb(uid))
        try:
            sql = "SELECT uid, score FROM %s WHERE uid = '%s';" % (self.witchScoreTable(uid), int(uid))
            m.Q(sql)
            rs = m.fetchone()
            if not rs:
                m.close()
                return False
            
            # log表规则是取uid倒数第2位分库 最后1位分表 共100个表（包括0）
            sql = "UPDATE %s SET score = score + %s, update_time = now() WHERE uid = '%s';" % (self.witchScoreTable(uid), score, int(uid))
            m.Q(sql)
        except:
            traceback.print_exc()
            m.close()
            return False
        
        # 如果今天有缓存，更新积分退款和减余额全部更新缓存
        r = m_redis.get_instance()
        r.delete(self._scoreListKey(uid))
        m.close()
        return True

    ############################################################################################################################


    