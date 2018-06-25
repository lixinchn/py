# -*- coding: UTF-8 -*-
'''
Created on 2015年10月10日

@author: lixin
'''
from ttypes import *
import urllib, traceback, json, datetime, time, math, re, random, hashlib
from lib.mysql_manager_rw import MysqlConn as mmysql
from lib.redis_manager import m_redis
from user_service.model_score_service import ScoreServiceHandle
from lib.json_manager import CJsonEncoder
from lib import ticket_manager
from base import BaseHandle


class UserAppServiceHandle(BaseHandle):
    def addUserAppActionLog(self, uid, device_id, action_log):
        dict_action_log = self._dirtyWorkAddUserAppActionLog(uid, device_id, action_log)
        if not dict_action_log:
            return False
        return self._insertAppLog(uid, device_id, dict_action_log)
        

    #################################################################################
    def _witchAppTable(self, uid):
        return "z_app_log_%s" % str(uid)[-1]

    def _dirtyWorkAddUserAppActionLog(self, uid, device_id, action_log):
        if not self._validate_param('uid', uid):
            return False
        if self.getUidByDeviceId(device_id) != uid:
            return False
        try:
            return json.loads(action_log)
        except:
            return False

    def _insertAppLog(self, uid, device_id, dict_action_log):
        m = mmysql(self.witchDb(uid))
        try:
            for pack_name, action in dict_action_log.items():
                sql = 'INSERT INTO %s (uid, device_id, pack_name, action, ctime) VALUES(%s, "%s", "%s", %s, NOW());' % (self._witchAppTable(uid), uid, device_id, pack_name, action)
                m.Q(sql)
        except Exception, e:
            m.close()
            return False
        m.close()
        return True