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

    ############################################################################################################################################
    # 获取用户首次下载的广告的价钱
    def test_1501_GetUserFirstAdScore(self):
        result = self.baseService.client.getUserFirstAdScore(self.uid)
        self.assertEqual(result, 0)

    # 什么都不存在的情况下，获取用户可用于小额兑换的广告次数
    def test_1502_GetUserSmallExchangeAllAdTime(self):
        result = self.baseService.client.getUserSmallExchangeAllAdTime(self.uid)
        result = json.loads(result)
        self.assertFalse('score_ad_time' in result)
        self.assertFalse('score_ad_holding_time' in result)
        self.assertFalse('score_ad_finish_time' in result)

    # add score
    def test_1503_AddScore_AD_ZiJia(self):
        sao = t_base.ScoreAddObj(client_ip = self.client_ip, trade_type = 1, uid = self.uid, order_id = '0', app_id = self.app_id, currency = 1500, pack_name = 'com.happy.lock.wifi',
                            action_type = 0, ad_name = '做测试用的', time_stamp = 120, device_id = self.device_id, os_type_id = 2)
        result = self.baseService.client.addScore(sao)
        self.assertTrue(result)

    # 获取用户可用于小额兑换的广告次数
    def test_1504_GetUserSmallExchangeAllAdTime(self):
        result = self.baseService.client.getUserSmallExchangeAllAdTime(self.uid)
        result = json.loads(result)
        self.assertEqual(result['score_ad_time'], 1)

    # 获取用户首次下载的广告的价钱
    def test_1505_GetUserFirstAdScore(self):
        result = self.baseService.client.getUserFirstAdScore(self.uid)
        self.assertEqual(result, 1500)

    # 在用户没有小额兑换广告余额的情况下，添加一个小额兑换
    def test_1506_AddSmallExchange_NoAdTime(self):
        result = self.baseService.client.addSmallExchange(self.uid, 'qb_500')
        self.assertFalse(result)

    # 添加一个金额不对的小额兑换
    def test_1507_AddSmallExchange_WrongScore(self):
        result = self.baseService.client.addSmallExchange(self.uid, 'qb_2000')
        self.assertFalse(result)

    # 增加一些小额兑换的广告次数
    def test_1508_AddScore_AD_ZiJia(self):
        result = True
        for i in range(0, 5):
            sao = t_base.ScoreAddObj(client_ip = self.client_ip, trade_type = 1, uid = self.uid, order_id = '0', app_id = self.app_id, currency = 1500, pack_name = 'com.happy.lock.wifi',
                                action_type = 0, ad_name = '做测试用的', time_stamp = 120, device_id = self.device_id, os_type_id = 2)
            result = result and self.baseService.client.addScore(sao)

        self.assertTrue(result)

    # 增加一个正确小额兑换
    def test_1509_AddSmallExchange(self):
        result = self.baseService.client.addSmallExchange(self.uid, 'qb_100')
        self.assertTrue(result)

    # 在已经存在一个小额兑换的情况下，再增加一个小额兑换
    def test_1510_AddSmallExchange_Repeat(self):
        result = self.baseService.client.addSmallExchange(self.uid, 'qb_500')
        self.assertFalse(result)

    # 存在一个小额兑换的情况下，获取用户可用于小额兑换的广告次数
    def test_1511_GetUserSmallExchangeAllAdTime(self):
        result = self.baseService.client.getUserSmallExchangeAllAdTime(self.uid)
        result = json.loads(result)
        self.assertEqual(result['score_ad_time'], 5)
        self.assertEqual(result['score_ad_holding_time'], 1)

    # 存在一个小额兑换的情况下，用一个错误的小额兑换来 finish
    def test_1512_FinishSmallExchange_wrong(self):
        result = self.baseService.client.finishSmallExchange(self.uid, 'qb_500', True)
        self.assertFalse(result)

    # 存在一个小额兑换的情况下，用正确的小额兑换金额来 finish，充值成功的情况
    def test_1513_FinishSmallExchange_right(self):
        result = self.baseService.client.finishSmallExchange(self.uid, 'qb_100', True)
        self.assertTrue(result)

    # finish 之后，检查一下可用于小额兑换的广告数量变化情况
    def test_1514_GetUserSmallExchangeAllAdTime_AfterFinish(self):
        result = self.baseService.client.getUserSmallExchangeAllAdTime(self.uid)
        result = json.loads(result)
        self.assertEqual(result['score_ad_time'], 5)
        self.assertEqual(result['score_ad_holding_time'], 0)
        self.assertEqual(result['score_ad_finish_time'], 1)

    # 增加一个正确小额兑换
    def test_1515_AddSmallExchange(self):
        result = self.baseService.client.addSmallExchange(self.uid, 'qb_500')
        self.assertTrue(result)

    # 检查一下可用于小额兑换的广告数量变化情况
    def test_1516_GetUserSmallExchangeAllAdTime_AfterFinish(self):
        result = self.baseService.client.getUserSmallExchangeAllAdTime(self.uid)
        result = json.loads(result)
        self.assertEqual(result['score_ad_time'], 0)
        self.assertEqual(result['score_ad_holding_time'], 5)
        self.assertEqual(result['score_ad_finish_time'], 1)

    # 存在一个小额兑换的情况下，用正确的小额兑换金额来 finish，充值失败的情况
    def test_1517_FinishSmallExchange_right(self):
        result = self.baseService.client.finishSmallExchange(self.uid, 'qb_500', False)
        self.assertTrue(result)

    # finish 之后，检查一下可用于小额兑换的广告数量变化情况
    def test_1518_GetUserSmallExchangeAllAdTime_AfterFinish(self):
        result = self.baseService.client.getUserSmallExchangeAllAdTime(self.uid)
        result = json.loads(result)
        self.assertEqual(result['score_ad_time'], 5)
        self.assertEqual(result['score_ad_holding_time'], 0)
        self.assertEqual(result['score_ad_finish_time'], 1)

    # 增加一个不是 ios 系统的加分
    def test_1519_AddScore_Not_IOS(self):
        sao = t_base.ScoreAddObj(client_ip = self.client_ip, trade_type = 1, uid = self.uid, order_id = '0', app_id = self.app_id, currency = 1500, pack_name = 'com.happy.lock.wifi',
                            action_type = 0, ad_name = '做测试用的', time_stamp = 120, device_id = self.device_id, os_type_id = 0)
        result = self.baseService.client.addScore(sao)
        self.assertTrue(result)

    # 验证上一个不是 ios 加分没有增加小额兑换的次数
    def test_1520_GetUserSmallExchangeAllAdTime_AfterNotIOS(self):
        result = self.baseService.client.getUserSmallExchangeAllAdTime(self.uid)
        result = json.loads(result)
        self.assertEqual(result['score_ad_time'], 6)
        self.assertEqual(result['score_ad_holding_time'], 0)
        self.assertEqual(result['score_ad_finish_time'], 1)

    # 增加一个特惠
    def test_1521_AddScore_Score_0(self):
        sao = t_base.ScoreAddObj(client_ip = self.client_ip, trade_type = 1, uid = self.uid, order_id = '0', app_id = self.app_id, currency = 0, pack_name = 'com.happy.lock.wifi',
                            action_type = 0, ad_name = '做测试用的', time_stamp = 120, device_id = self.device_id, os_type_id = 0)
        result = self.baseService.client.addScore(sao)
        self.assertTrue(result)

    # 特惠不增加小额兑换的广告次数
    def test_1522_GetUserSmallExchangeAllAdTime_AfterScore0(self):
        result = self.baseService.client.getUserSmallExchangeAllAdTime(self.uid)
        result = json.loads(result)
        self.assertEqual(result['score_ad_time'], 6)
        self.assertEqual(result['score_ad_holding_time'], 0)
        self.assertEqual(result['score_ad_finish_time'], 1)

    # 直接扣减下载广告的次数
    def test_1523_ConsumeAdDownloadTimes_Succ(self):
        result = self.baseService.client.consumeAdDownloadTimes(self.uid, 2)
        self.assertTrue(result)
        result = self.baseService.client.getUserSmallExchangeAllAdTime(self.uid)
        result = json.loads(result)
        self.assertEqual(result['score_ad_time'], 4)
        self.assertEqual(result['score_ad_holding_time'], 0)
        self.assertEqual(result['score_ad_finish_time'], 3)

    # 直接扣减下载广告的次数，不成功
    def test_1524_ConsumeAdDownloadTimes_Fail(self):
        result = self.baseService.client.consumeAdDownloadTimes(self.uid, 1000)
        self.assertFalse(result)
        result = self.baseService.client.getUserSmallExchangeAllAdTime(self.uid)
        result = json.loads(result)
        self.assertEqual(result['score_ad_time'], 4)
        self.assertEqual(result['score_ad_holding_time'], 0)
        self.assertEqual(result['score_ad_finish_time'], 3)



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