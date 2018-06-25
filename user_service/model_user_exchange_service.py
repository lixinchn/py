# -*- coding: UTF-8 -*-
'''
Created on 2015年8月18日

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


class UserExchangeServiceHandle(BaseHandle):
    SMALL_EXCHANGE_ALL_AD_TIME_CACHE_TIME = 60 * 20
    SMALL_EXCHANGE_FIRST_AD_SCORE_CACHE_TIME = 60 * 60 * 24 * 3

    # 小额兑换需要消耗的金额列表
    SMALL_EXCHANGE_SCORE_AD_TIME_LIST = {
        'qb_100': 1,
        'qb_500': 5,
        'mobile_100': 1,
        'mobile_500': 5,
    }

    def getUserSmallExchangeAllAdTime(self, uid):
        all_ad_time_data = '{}'
        if not self._validate_param('uid', uid):
            return all_ad_time_data
        r = m_redis.get_instance()
        m = mmysql()
        redis_key = m_redis._ZHUAN_USER_SMALL_EXCHANGE_ALL_AD_TIME_ + str(uid)
        all_ad_time_data = r.get(redis_key)
        if not all_ad_time_data:
            sql = 'SELECT score_ad_time, score_ad_finish_time, score_ad_holding_time FROM user_small_exchange_%s WHERE uid = %s;' % (self._whichTable(uid), uid)
            m.Q(sql)
            rs = m.fetchone()
            if not rs:
                rs = self.SMALL_EXCHANGE_SCORE_AD_TIME_LIST
            else:
                rs.update(self.SMALL_EXCHANGE_SCORE_AD_TIME_LIST)
            r.set(redis_key, json.dumps(rs if rs else all_ad_time_data, cls = CJsonEncoder), self.SMALL_EXCHANGE_ALL_AD_TIME_CACHE_TIME)
            all_ad_time_data = r.get(redis_key)
        m.close()
        return all_ad_time_data

    def getUserFirstAdScore(self, uid):
        return self._getUserSmallExchangeTime(uid, m_redis._ZHUAN_USER_FIRST_AD_SCORE_, 'first_ad_score', self.SMALL_EXCHANGE_FIRST_AD_SCORE_CACHE_TIME)

    def addSmallExchange(self, uid, type_score):
        if not self._addSmallExchangeDirtyWork(uid, type_score):
            return False

        # 到这里说明可以进行小额兑换，那么充值一下数据
        r = m_redis.get_instance()
        m = mmysql()
        ad_time = self.SMALL_EXCHANGE_SCORE_AD_TIME_LIST.get(type_score)
        redis_key = m_redis._ZHUAN_USER_SMALL_EXCHANGE_ALL_AD_TIME_ + str(uid)
        r.delete(redis_key)
        sql = 'UPDATE user_small_exchange_%s SET score_ad_time = score_ad_time - %s, score_ad_holding_time = %s WHERE uid = %s;' % (self._whichTable(uid), ad_time, ad_time, uid)
        result = m.Q(sql)
        m.close()
        return result

    def finishSmallExchange(self, uid, type_score, succ):
        r = m_redis.get_instance()
        if not self._finishSmallExchangeDirtyWork(r, uid, type_score):
            return False

        # 到这里说明可以进行小额兑换完毕的操作，处理一下数据
        r = m_redis.get_instance()
        m = mmysql()
        ad_time = self.SMALL_EXCHANGE_SCORE_AD_TIME_LIST.get(type_score)
        redis_key = m_redis._ZHUAN_USER_SMALL_EXCHANGE_ALL_AD_TIME_ + str(uid)
        r.delete(redis_key)
        if succ:
            sql = 'UPDATE user_small_exchange_%s SET score_ad_holding_time = 0, score_ad_finish_time = score_ad_finish_time + %s WHERE uid = %s;' % (self._whichTable(uid), ad_time, uid)
        else:
            sql = 'UPDATE user_small_exchange_%s SET score_ad_holding_time = 0, score_ad_time = score_ad_time + %s WHERE uid = %s;' % (self._whichTable(uid), ad_time, uid)
        result = m.Q(sql)
        m.close()
        return result

    def consumeAdDownloadTimes(self, uid, times):
        if not self._validate_param('uid', uid):
            return False
        all_ad_time_data = json.loads(self.getUserSmallExchangeAllAdTime(uid))
        score_ad_time = all_ad_time_data.get('score_ad_time', 0)
        if score_ad_time < times:
            return False
        m = mmysql()
        sql = 'UPDATE user_small_exchange_%s SET score_ad_time = score_ad_time - %s, score_ad_finish_time = score_ad_finish_time + %s WHERE uid = %s;' % (self._whichTable(uid), times, times, uid)
        result = m.Q(sql)
        m.close()
        if result:
            r = m_redis.get_instance()
            redis_key = m_redis._ZHUAN_USER_SMALL_EXCHANGE_ALL_AD_TIME_ + str(uid)
            r.delete(redis_key)
        return result

    ###############################################################################################
    def _whichTable(self, uid):
        return str(uid)[-1:]

    def _cacheSmallExchangeData(self, r, redis_key, redis_value, cache_time):
        r.set(redis_key, redis_value, cache_time)

    def _getUserSmallExchangeTime(self, uid, redis_key_prefix, db_column, cache_time):
        self._validate_param('uid', uid)
        r = m_redis.get_instance()
        m = mmysql()
        redis_key = redis_key_prefix + str(uid)
        s_time = r.get(redis_key)
        if not s_time:
            sql = 'SELECT %s FROM user_small_exchange_%s WHERE uid = %s;' % (db_column, self._whichTable(uid), uid)
            m.Q(sql)
            rs = m.fetchone()
            if rs and rs[db_column]:
                s_time = rs[db_column]
            else:
                s_time = 0
            self._cacheSmallExchangeData(r, redis_key, s_time, cache_time)
            s_time = r.get(redis_key)
        m.close()
        return int(s_time)

    def _addScoreSmallExchangeWork(self, uid, ScoreAddObj, currency):
        # 如果加分类型不是广告，直接返回
        if ScoreAddObj.action_type != Scoretype._ACTION_TYPE_AD:
            return
        # 如果广告不是自家的，直接返回
        if ScoreAddObj.trade_type != 1:
            return
        '''
        # 如果不是 ios 系统，直接返回
        if ScoreAddObj.os_type_id != OS_TYPE._OS_TYPE_IOS:
            return
        '''

        # 如果金额为0(特惠)，直接返回
        if currency == 0:
            return

        m = mmysql()
        r = m_redis.get_instance()
        self._firstAdWork(m, r, uid, currency) # 先看看是不是第一次下载广告
        self._addSmallExchangeAdTime(m, r, uid) # 增加用户可用于小额兑换的广告次数
        m.close()

    def _firstAdWork(self, m, r, uid, currency):
        # 如果用户的注册时间在该功能的上线时间之前，那么第一次下载广告对于他来说就没有意义。这里判断一下用户的注册时间
        user_info = self.getUserInfoByUid(uid)
        if user_info.ctime < '2015-09-01': # TODO: 要改成上线时间
            sql = 'INSERT INTO user_small_exchange_%s(uid, first_ad_score) VALUES(%s, -1) ON DUPLICATE KEY UPDATE first_ad_score = -1;' % (self._whichTable(uid), uid)
            m.Q(sql)
            return

        # 如果用户是第一次下载广告，那么设置一下 user_small_exchange 表中 first_ad_score 字段为第一次广告的金额
        redis_key = m_redis._ZHUAN_USER_FIRST_AD_SCORE_ + uid
        first_ad_score = int(r.get(redis_key)) if r.get(redis_key) != None else None
        if first_ad_score: # 用户之前下载过广告，直接返回
            return

        # 走到这里说明没有缓存，再去数据库里查一下
        sql = 'SELECT first_ad_score FROM user_small_exchange_%s WHERE uid = %s;' % (self._whichTable(uid), uid)
        m.Q(sql)
        rs = m.fetchone()
        if not rs or not rs['first_ad_score']: # 没有该 uid 的记录或者 first_ad_score 为0
            r.delete(redis_key)
            sql = 'INSERT INTO user_small_exchange_%s(uid, first_ad_score) VALUES(%s, %s) ON DUPLICATE KEY UPDATE first_ad_score = %s;' % (self._whichTable(uid), uid, currency, currency)
            m.Q(sql)

    def _addSmallExchangeAdTime(self, m, r, uid):
        redis_key = m_redis._ZHUAN_USER_SMALL_EXCHANGE_ALL_AD_TIME_ + uid
        r.delete(redis_key)
        sql = 'INSERT INTO user_small_exchange_%s(uid, score_ad_time) VALUES(%s, 1) ON DUPLICATE KEY UPDATE score_ad_time = score_ad_time + 1;' % (self._whichTable(uid), uid)
        m.Q(sql)


    # 用户是否可以进行小额兑换的检查方法
    # 1. 如果 uid 格式不对，不允许进行小额兑换
    # 2. 如果小额兑换的金额不在默认列表中，不允许进行小额兑换
    # 3. 如果有进行中的小额兑换，就不允许用户再次进行小额兑换
    # 4. 如果小额兑换需要消耗的广告数量不足，不允许用户进行小额兑换
    def _addSmallExchangeDirtyWork(self, uid, type_score):
        if not self._validate_param('uid', uid):
            return False
        if not type_score in self.SMALL_EXCHANGE_SCORE_AD_TIME_LIST:
            return False
        all_ad_time_data = json.loads(self.getUserSmallExchangeAllAdTime(uid))
        score_ad_time = all_ad_time_data.get('score_ad_time', 0)
        score_ad_holding_time = all_ad_time_data.get('score_ad_holding_time', 0)

        if score_ad_holding_time != 0:
            return False
        if score_ad_time < self.SMALL_EXCHANGE_SCORE_AD_TIME_LIST.get(type_score):
            return False
        return True

    # 用户完成小额兑换的检查方法
    # 1. 如果 uid 格式不对，不允许进行小额兑换
    # 2. 如果小额兑换的金额不在默认列表中，不允许进行小额兑换
    # 3. 如果用户正在进行中的小额兑换消耗的广告数跟 type_score 代表的广告数不匹配
    def _finishSmallExchangeDirtyWork(self, r, uid, type_score):
        if not self._validate_param('uid', uid):
            return False
        if not type_score in self.SMALL_EXCHANGE_SCORE_AD_TIME_LIST:
            return False
        redis_key = m_redis._ZHUAN_USER_SMALL_EXCHANGE_ALL_AD_TIME_ + str(uid)
        r.delete(redis_key)
        all_ad_time_data = json.loads(self.getUserSmallExchangeAllAdTime(uid))
        score_ad_holding_time = all_ad_time_data.get('score_ad_holding_time', 0)
        if score_ad_holding_time == 0: # 不存在正在进行的小额兑换
            return False
        if self.SMALL_EXCHANGE_SCORE_AD_TIME_LIST.get(type_score, -1) != score_ad_holding_time:
            return False
        return True

