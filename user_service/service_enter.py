# -*- coding: UTF-8 -*-
'''
Created on 2015年3月5日

@author: lixin
'''
import UserService
from ttypes import *
from public.ttypes import *
import urllib,traceback,json,datetime,time,math,re,random
from lib.mysql_manager_rw import MysqlConn as mmysql
from lib.redis_manager import m_redis
from user_service.model_user_service import UserServiceHandle
from user_service.model_score_service import ScoreServiceHandle
from user_service.model_user_login_service import UserLoginServiceHandle
from user_service.model_user_ex_service import UserExServiceHandle
from user_service.model_user_exchange_service import UserExchangeServiceHandle
from user_service.model_user_app_service import UserAppServiceHandle
from ttypes import InvalidOperation


class ServiceHandle(UserServiceHandle, ScoreServiceHandle, UserLoginServiceHandle, UserExServiceHandle, UserExchangeServiceHandle, UserAppServiceHandle):
    def __init__(self):
        print 'init___'
        pass

    def ping(self,str):
        print 'ping'
        r = m_redis.get_instance()
        r.set('xx', int(r.get('xx') or 0) + 1, 300)
        print r.get('xx')
        return True
 