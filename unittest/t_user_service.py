# -*- coding: UTF-8 -*-
# author: lixin
import t_base
import random
import math
import unittest
import time, json, datetime


class UserTest(unittest.TestCase):
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

    # 成功添加用户
    def test_1000_AddUser(self):
        self.assertNotEqual(self.uid, 0, 'add user')

    # 获取用户信息
    def test_1001_GetUser(self):
        userInfo = self.baseService.client.getUserInfoByUid(self.uid, '', 0, 0)
        self.assertEqual(self.device_id, userInfo.device_id, 'get user info')
        self.assertEqual(self.mobile, userInfo.mobile, 'get user info')

    # 用户登录
    def test_1002_UserLogin(self):
        result = self.baseService.client.userLogin(self.mobile, self.pw, self.device_id, self.os_type, self.client_ip, self.app_id, self.imsi, self.channel)
        self.assertTrue(result.islogin)

    # valiadate use token
    def test_1003_ValidateUserToken(self):
        loginResult = self.baseService.client.userLogin(self.mobile, self.pw, self.device_id, self.os_type, self.client_ip, self.app_id, self.imsi, self.channel)
        validateResult = self.baseService.client.validateUserToken(loginResult.ticket, self.app_id)
        self.assertEqual(validateResult.uid, self.uid)

    # update device_id
    def test_1004_UpdateDeviceId(self):
        now = time.time()
        new_device_id = '%d%s' % (now, 'rand')
        result = self.baseService.client.updateUserDeviceId(self.uid, self.device_id, new_device_id, self.app_id)
        self.assertTrue(result)
        userInfo = self.baseService.client.getUserInfoByUidAllUser(self.uid, '', 0, 0)
        self.assertEqual(userInfo.device_id, new_device_id)
        retult = self.baseService.client.updateUserDeviceId(self.uid, new_device_id, self.device_id, self.app_id)
        self.assertTrue(result)
        userInfo = self.baseService.client.getUserInfoByUidAllUser(self.uid, '', 0, 0)
        self.assertEqual(userInfo.device_id, self.device_id)
        
    # update user status
    def test_1005_UpdateUserStatus(self):
        userInfo = self.baseService.client.getUserInfoByUidAllUser(self.uid, '', 0, 0)
        self.assertEqual(userInfo.status, 1)
        result = self.baseService.client.updateUserStatus(self.uid, 0)
        self.assertTrue(result)
        userInfo = self.baseService.client.getUserInfoByUidAllUser(self.uid, '', 0, 0)
        self.assertEqual(userInfo.status, 0)
        result = self.baseService.client.updateUserStatus(self.uid, 1)
        self.assertTrue(result)
        userInfo = self.baseService.client.getUserInfoByUidAllUser(self.uid, '', 0, 0)
        self.assertEqual(userInfo.status, 1)

    # update user password
    def test_1006_UpdateuserPassword(self):
        newPassword = u'123456'
        updateResult = self.baseService.client.updateUserPassword(newPassword, self.uid, self.mobile)
        self.assertTrue(updateResult)
        loginResult = self.baseService.client.userLogin(self.mobile, newPassword, self.device_id, self.os_type, self.client_ip, self.app_id, self.imsi, self.channel)
        self.assertTrue(loginResult.islogin)
        newUpdateResult = self.baseService.client.updateUserPassword(self.pw, self.uid, self.mobile)
        self.assertTrue(newUpdateResult)
        newLoginRetuls = self.baseService.client.userLogin(self.mobile, self.pw, self.device_id, self.os_type, self.client_ip, self.app_id, self.imsi, self.channel)
        self.assertTrue(newLoginRetuls.islogin)
        
    # 获取用户当月积分变化情况的次数
    def test_1007_GetUserThisMonthScoreList(self):
        result = self.baseService.client.getUserThisMonthScoreTime(84184998, 0)
        #return 1
        self.assertEqual(result, 0)

    # add score
    def test_1008_AddScore_AD_WALL_20(self):
        sao = t_base.ScoreAddObj(client_ip = self.client_ip, trade_type = 0, uid = self.uid, order_id = '0', app_id = self.app_id, currency = 1500, pack_name = 'com.happy.lock.wifi',
                            action_type = 10, ad_name = '做测试用的', time_stamp = 120, device_id = self.device_id)
        result = self.baseService.client.addScore(sao)
        # result = True
        self.assertTrue(result)

    # modify user mobile
    def test_1009_ModifyUserMobile(self):
        # 只有手机号为 200 开头的(web 版)才可以更改
        result = self.baseService.client.updateUserMobile(self.uid, 18888851481)
        # self.assertEqual(result, '')

    # 获取用户余额列表
    def test_1010_GetUserScoreList_AD_WALL_20(self):
        result = self.baseService.client.getUserScoreList(self.uid)
        self.assertEqual(result['ad_wall_20'], 1500)

    # add score
    def test_1012_AddScore_AD(self):
        sao = t_base.ScoreAddObj(client_ip = self.client_ip, trade_type = 0, uid = self.uid, order_id = '0', app_id = self.app_id, currency = 1500, pack_name = 'com.happy.lock.wifi',
                            action_type = 0, ad_name = '做测试用的', time_stamp = 120, device_id = self.device_id)
        result = self.baseService.client.addScore(sao)
        self.assertTrue(result)

    # 获取用户 7 天内是否下载过广告或者有邀请行为
    def test_1013_CheckUserAdOrInviteInSevenDays(self):
        date = time.strftime("%Y-%m-%d", time.localtime())
        result = self.baseService.client.checkUserAdOrInviteInSevenDays(self.uid, str(date))
        self.assertTrue(result)

    # existAppRegister
    def test_1014_ExistAppRegister(self):
        result = self.baseService.client.existAppRegister(self.uid, 0)
        self.assertFalse(result)

    # 平衡用户收支
    def test_1015_ResumeUserScoreForExchange(self):
        result = self.baseService.client.resumeUserScoreForExchange(int(self.uid), 200)
        self.assertTrue(result)

    # 更改用户手机号
    def test_1016_UpdateUserMobileForAdmin(self):
        new_mobile = (int)(random.random() * 100000000000L)
        result = self.baseService.client.updateUserMobileForAdmin(int(self.uid), self.mobile, new_mobile)
        self.assertEqual(result, '')
        userInfo = self.baseService.client.getUserInfoByUid(self.uid, '', 0, 0)
        self.assertEqual(new_mobile, userInfo.mobile)

    # 更改用户手机号，失败
    def test_1017_UpdateUserMobileForAdmin(self):
        result = self.baseService.client.updateUserMobileForAdmin(int(self.uid), self.mobile, self.mobile)
        self.assertTrue(result != '')

    # 免手机号注册，8位uid
    def test_1018_AddUser(self):
        now = time.time()
        app_id = 1
        pw = u'123456'
        os_type = 'android'
        channel = 'wall_1350'
        client_ip = '127.0.0.1'
        imsi = '460036090242700'
        device_id = '%d%s' % (now, 'rand')
        mobile = 0
        user = t_base.UserAddObj(client_ip = client_ip, pnum = mobile, pw = pw, app_id = app_id, channel = channel, os_type = os_type,
                            ic = '60942757', imsi = imsi, device_id = device_id)
        uid = self.baseService.client.addUser(user)
        self.assertEqual(len(str(uid)), 8)


if __name__ == '__main__':
    unittest.main()


# add user point
def addUserPoint(uid):
    print b.client.updateUserPoint(uid, 1, 30)

# get user point
def getUserPoint(uid):
    print b.client.getUserPointById(uid)


#uid = addUser()
#getUserPoint(60942757)
#addUserPoint(60942757)
#getUserPoint(60942757)

#getUserPoint(70076020)
#addUserPoint(70076020)
#getUserPoint(70076020)

# print b.client.getUserInfoByUid(uid, '', 0, 0)

#getUserPoint(60942757)