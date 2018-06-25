# -*- coding: UTF-8 -*-
# author: lixin
import t_base
import random
import math
import unittest
import time, json, datetime


class UserAppTest(unittest.TestCase):
    # 初始化
    @classmethod
    def setUpClass(self):
        self.baseService = t_base.BaseService()
        now = time.time()
        self.app_id = 1
        self.pw = u'123456'
        self.os_type = 'android'
        self.channel = 'wall_1350'
        self.client_ip = '127.0.0.1'
        self.imsi = '460036090242703'
        self.device_id = '%d%s' % (now, 'rand')
        self.mobile = (int)(random.random() * 100000000000L)
        user = t_base.UserAddObj(client_ip = self.client_ip, pnum = self.mobile, pw = self.pw, app_id = self.app_id, channel = self.channel, os_type = self.os_type,
                            ic = '60942757', imsi = self.imsi, device_id = self.device_id)
        self.uid = self.baseService.client.addUser(user)

    # 退出清理
    @classmethod
    def tearDownClass(self):
        pass

    ############################################################################################################################################
    # 获取用户首次下载的广告的价钱
    def test_1601_AddUserAppActionLog(self):
        action_log = {'com.app.test': 0, 'com.app.aaa': 1, 'com.app.bbb': 0, 'com.app.ccc': 0}
        result = self.baseService.client.addUserAppActionLog(self.uid, self.device_id, json.dumps(action_log))
        self.assertTrue(result)

    # 空
    def test_1602_AddUserAppActionLog_None(self):
        action_log = {}
        result = self.baseService.client.addUserAppActionLog(self.uid, self.device_id, json.dumps(action_log))
        self.assertFalse(result)

    # not json
    def test_1603_AddUserAppActionLog_NotJson(self):
        action_log = {}
        result = self.baseService.client.addUserAppActionLog(self.uid, self.device_id, '{jjj')
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()