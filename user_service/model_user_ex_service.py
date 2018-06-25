# -*- coding: UTF-8 -*-
'''
Created on 2015年3月5日

@author: zh
'''


# from ttypes import InvalidOperation
# from ttypes import UserInfo as UInfo
from ttypes import workSpace,UserExInfo

import urllib,traceback,json,datetime,time,math,re,random,hashlib
from lib.mysql_manager_rw import MysqlConn as mmysql
from lib.redis_manager import m_redis
from user_service.model_score_service import ScoreServiceHandle
from lib.json_manager import CJsonEncoder
from ttypes import InvalidOperation
from base import BaseHandle

class UserExServiceHandle(BaseHandle):
    '''
    classdocs
    '''
    
    def test(self,str):
        print str
        return True
    
    #   滑屏时间间隔配置
    def getUserExInfo(self,uid):
        uid = int(uid)
        r = m_redis.get_instance("ad")
        key = m_redis._ZHUAN_USER_EX_INFO_+ str(uid)
        uinfo_str = r.get(key)
        if uinfo_str:
            uinfo_obj = json.loads(uinfo_str)
        else:
            m = mmysql()
            sql = "select uid,sex,workspace,birth_day,ctime from z_user_info_ex where uid = '%s'"%(uid)
            m.Q(sql)
            uinfo_obj = m.fetchone()
            if uinfo_obj:
                uinfo_str = json.dumps(uinfo_obj,cls=CJsonEncoder)
                r.set(key,uinfo_str,86400)
                uinfo_obj = json.loads(uinfo_str)
            else:
                uinfo_obj = {}
                r.set(key,"{}",300)
            m.close()
        
        if not uinfo_obj:
            return UserExInfo()
        else:
            uei = UserExInfo()
            uei.uid = uinfo_obj["uid"]
            uei.sex = uinfo_obj["sex"]
            uei.workspace = uinfo_obj["workspace"]
            uei.birthday = uinfo_obj["birth_day"]
            uei.ctime = uinfo_obj["ctime"]
            return uei
    
    def createUserExInfo(self,userexinfo):
        
        if not re.findall("^\d{8,10}$", str(userexinfo.uid)):
            raise  InvalidOperation(1,"uid is not validate.")

        if userexinfo.sex not in [1,2]:
            raise  InvalidOperation(2,"sex is not validate.")
        
        if not workSpace._VALUES_TO_NAMES.has_key(userexinfo.workspace):
            raise  InvalidOperation(3,"workSpace is not validate.")
        
        if not re.findall("^\d{4}-\d{2}-\d{2}$", userexinfo.birthday):
            raise  InvalidOperation(4,"birth day is not validate.")
        
        try:
            m = mmysql()
            sql = "insert into z_user_info_ex(uid,sex,workspace,birth_day,ctime) values('%s','%s','%s','%s',now())"%(userexinfo.uid,userexinfo.sex,userexinfo.workspace,userexinfo.birthday)
            m.Q(sql)
            m.close()
            key = m_redis._ZHUAN_USER_EX_INFO_+ str(userexinfo.uid)
            r = m_redis.get_instance("ad")
            r.delete(key)
        except:
            raise  InvalidOperation(5,traceback.format_exc())
        
        return True



