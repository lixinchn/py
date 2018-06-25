# -*- coding: UTF-8 -*-
'''
redis缓存管理类

@author: zh

增加了连接池，不过因为要兼容之前的，所以看起来很肿。。。
'''
import redis
import re,random,sys
from tornado.options import options

_REDIS_CONN_NUM = 5
# _REDIS_CONN_NUM = 1

_REDIS=[]
for i in range(_REDIS_CONN_NUM):
    _REDIS.append( redis.Redis(host=options.redis_host,
                         port=options.redis_port,
                         db=options.redis_db))
_REDIS_HOST_LIST = {}


def load_redis_conf(rhlsa):
    conn_arr = []
    for i in range(_REDIS_CONN_NUM):
        conn_arr.append(redis.Redis(host=getattr(options, "redis_" + rhlsa + "_host"),
                                          port=getattr(options, "redis_" + rhlsa + "_port"),
                                          db=getattr(options, "redis_" + rhlsa + "_db"))
                         )
    _REDIS_HOST_LIST[rhlsa] = conn_arr


if options.redis_host_name_list and options.redis_host_name_list != "":
    _REDIS_HOST_LIST_STR_ARR = options.redis_host_name_list.split(",")

    for rhlsa in _REDIS_HOST_LIST_STR_ARR:
        special_tag = re.findall("\[(.+)\]", rhlsa)
        if special_tag:
            special_tag = special_tag[0]
            db_tag = rhlsa.replace(re.findall("(\[.+\])", rhlsa)[0], "")
            db_tag_arr = []
            analyse_num_tag = re.findall("([0-9]+)\-([0-9]+)", special_tag)
            if analyse_num_tag:
                db_tag_arr = [x for x in range(int(analyse_num_tag[0][0]), int(analyse_num_tag[0][1]) + 1)]
                special_tag = special_tag.replace(re.findall("([0-9]+\-[0-9]+)", special_tag)[0], "")
            if len(special_tag) > 0:
                for x in special_tag:
                    db_tag_arr.append(x)
            if db_tag_arr:
                for db_sub_tag in db_tag_arr:
                    load_redis_conf(db_tag + str(db_sub_tag))
        else:
            load_redis_conf(rhlsa)

class m_redis(object):
    '''
    classdocs
    '''
    _CACHE_EXPIRE = 7200
    #广告墙去重
    _ZHUAN_RECEIVE_AD_WALL_ORDER_MSG_ = "_ZHUAN_R_A_W_O_M_"
    #划屏加分去重复
    _ZHUAN_RECEIVE_RIGHT_CATCH_ = "_ZHUAN_R_R_C_"
    _ZHUAN_RECEIVE_RIGHT_CATCH_TIME_ = "_ZHUAN_R_R_C_T_"
    _ZHUAN_RECEIVE_RIGHT_CATCH_PROBABILITY_ = "_ZHUAN_R_R_C_P_"
    _ZHUAN_RECEIVE_RIGHT_CATCH_HOW_MANY_ = "_ZHUAN_R_R_C_H_M_"
    _ZHUAN_RECEIVE_RIGHT_CATCH_HOW_MANYG_ = "_ZHUAN_R_R_C_H_MG_"
    #用户右划中奖得到的分数
    _ZHUAN_RECEIVE_RIGHT_CATCH_SCORE_ = "_ZHUAN_R_R_C_S_"
    #防止重复提交加分
    _ZHUAN_RECEIVE_RIGHT_CATCH_NOT_REPEAT_ = "_ZHUAN_R_R_C_S_N_R_"
    #防止重复提交加分
    _ZHUAN_RECEIVE_LEFT_CATCH_NOT_REPEAT_ = "_ZHUAN_R_L_C_S_N_R_"
    #左划广告id和广告价格对应
    _ZHUAN_LEFT_AD_PRICE_FROM_ADID_ = "_ZHUAN_LEFT_A_P_F_A_"
    
    _ZHUAN_USER_SCORE_LIST_ = "_ZHUAN_U_S_L_"
    _ZHUAN_USER_SCORE_LIST_GROUP_ = "_ZHUAN_U_S_L_G_"
    
    _ZHUAN_MSG_SEND_TIME_ = "_ZHUAN_M_S_T_"
    
    _ZHUAN_VALIDATE_CODE_ = "_ZHUAN_V_C_"
    
    _ZHUAN_REGISTER_ = "_ZHUAN_R_"
    
    _ZHUAN_USER_LOGIN_NEW_ = "_ZHUAN_U_L_N2_"
    
    _ZHUAN_APP_ID_ = "_ZHUAN_A_I_"
    
    _ZHUAN_USER_MSG_ = "_ZHUAN_U_M"
    #UID 和 deviceid 的对应关系
    _ZHUAN_USER_ID_BY_DEVICE_ID_ = "_ZHUAN_U_I_B_D_I"
    _ZHUAN_USER_ID_BY_PNUM_ = "_ZHUAN_U_P"
    _ZHUAN_PNUM_BY_USER_ID_ = "_ZHUAN_P_U"
    #邀请数
    _ZHUAN_INVITE_MEMBER_ = "_ZHUAN_INVITE_MEMBER_"
    #测试uid缓存
    _ZHUAN_TEST_USER_ = "_ZHUAN_TEST_USER_"
    #允许登陆的device_id列表
    _ZHUAN_USER_ID_BY_DEVICE_ID_LIST_ = "_ZHUAN_U_I_B_D_I_LIST"
    #用户反馈时间控制
    _ZHUAN_USER_REPORT_ = "_ZHUAN_USER_REPORT_"
    
    _ZHUAN_AD_CACHE_ = "_ZHUAN_AD_CACHE_" 
    
    _ZHUAN_COUNTING_BUY_PRO_ = "_ZHUAN_COUNTING_B_P_" 
    
    _ZHUAN_TODAY_USER_SCORE_ = "_ZHUAN_T_U_S_"
    
    _ZHUAN_TODAY_USER_SCORE_NEW_ = "_ZHUAN_T_U_S_N_"
    
    _ZHUAN_USER_SCORE_ALL_LIST_ = "_ZHUAN_U_S_A_L_"
    #用户受监控的分数，这部分分数是一个阈值，超过这个阈值会特殊处理
    _ZHUAN_USER_SCORE_MAX_ = "_ZHUAN_USER_SCORE_MAX_"
    #重新绑定设备的验证码
    _ZHUAN_BIND_PHONE_CHECK_CODE_ = "_ZHUAN_BIND_P_C_C_"
    #黑名单ip段
    _ZHUAN_USER_BLACK_IP_ = "_ZHUAN_USER_BLACK_IP_"

    #需要进小黑屋黑名单channel
    _ZHUAN_XIAOHEIWU_CHANNEL_ = "_ZHUAN_XIAOHEIWU_CHANNEL_"
    
    #需要进小黑屋黑名单channel
    _ZHUAN_SYS_CONF_ = "_ZHUAN_SYS_CONF_"
    
    #任务是否已经完成标记
    _ZHUAN_QUEST_FINISH_ = "_ZHUAN_QUEST_FINISH_"
    
    #新消息标记 存储最后一次查询的消息id  有新消息就清楚此缓存
    _ZHUAN_MSG_SELECT_ID_ = "_ZHUAN_MSG_SELECT_ID_"
    
    #公共新消息标记 存储最后一次查询的消息id  有新消息就清楚此缓存
    _ZHUAN_PUBLIC_MSG_SELECT_ID_ = "_ZHUAN_P_MSG_SELECT_ID_"
    #缓存公共消息内容
    _ZHUAN_PUBLIC_MSG_CACHE_ = "_ZHUAN_PUBLIC_MSG_CACHE_"
    
    #打包用的计数缓存 其实只需要解决5分钟内的冲突问题 5分钟还没打好肯定是有问题的
    _ZHUAN_PK_PACKAGE_CACHE_ = "_ZHUAN_PK_PACKAGE_CACHE_"
    
    #用户是否被hold住  hold住的用户加分更加严格
    _ZHUAN_HOLD_USER_ID_ = "_ZHUAN_HOLD_USER_ID_"
    
    #用户任务列表缓存
    _ZHUAN_QUEST_LIST_USER_ = "_ZHUAN_QUEST_LIST_USER_"
    
    #ios用户签到
    _ZHUAN_IOS_SIGN_IN_ = "_ZHUAN_SIGN_IN_"
    #ios用户签到次数
    _ZHUAN_IOS_SIGN_IN_NUM_ = "_ZHUAN_IOS_SIGN_IN_NUM_"
    #ios用户签到
    _ZHUAN_IOS_LOTTERY_DRAW_ = "_ZHUAN_IOS_LOTTERY_DRAW_"
    #ios用户签到次数
    _ZHUAN_IOS_LOTTERY_DRAW_NUM_ = "_ZHUAN_IOS_LOTTERY_DRAW_NUM_"
    #ios用户签到得分
    _ZHUAN_IOS_SIGN_IN_SCORE_ = "_ZHUAN_IOS_SIGN_IN_SCORE_"
    #ios用户抽奖得分
    _ZHUAN_IOS_LOTTERY_DRAW_SCORE_ = "_ZHUAN_IOS_LOTTERY_DRAW_SCORE_"
    #app 更新接口
    _ZHUAN_USER_VERSION_UPDATE_ = "_ZHUAN_USER_VERSION_UPDATE_"
    #app banner 广告
    _ZHUAN_AD_BANNER_ = "_ZHUAN_AD_BANNER_"
    #ios  widget 广告
    _ZHUAN_IOS_WIDGET_ = "_ZHUAN_IOS_WIDGET_"
    # test package
    _ZHUAN_TEST_PKG = "_ZHUAN_TEST_PKG_"

    # 存放公有游戏消息配置
    _ZHUAN_GAMEMSG_CFG_ ='_ZHUAN_GAMEMSG_CFG_'
    # 存放公有游戏消息码资源
    _ZHUAN_GAMEMSG_DATA_ ='_ZHUAN_GAMEMSG_DATA_'
    
    # 存放android push 用户消息
    _ZHUAN_PUSH_USER_MSG_ ='_ZHUAN_PUSH_USER_MSG_'
    # 存放android push 公共消息
    _ZHUAN_PUSH_PUB_MSG_ ='_ZHUAN_PUSH_PUB_MSG_'
    # 存放android push 公共消息 已阅读记录
    _ZHUAN_PUSH_PUB_MSG_EX_ ='_ZHUAN_PUSH_PUB_MSG_EX_'
    # 存放android push 消息 已阅读记录统计
    _ZHUAN_PUSH_PUB_MSG_COUNT_ ='_ZHUAN_PUSH_PUB_MSG_COUNT_'
    # 存放android push 消息 已阅读记录统计
    _ZHUAN_USER_POINT_ ='_ZHUAN_USER_POINT_'
    # 存放用户扩展信息
    _ZHUAN_USER_EX_INFO_ ='_ZHUAN_USER_EX_INFO_'

    # 用户当月加分的次数(自然月)
    _ZHUAN_USER_SCORE_TIME_THIS_MONTH_ = '_ZHUAN_USER_SCORE_TIME_THIS_MONTH_'

    # 用户小额兑换相关的广告数量
    _ZHUAN_USER_SMALL_EXCHANGE_ALL_AD_TIME_ = '_ZHUAN_USER_SMALL_EXCHANGE_ALL_AD_TIME_'

    # 用户首次下载的广告的价钱
    _ZHUAN_USER_FIRST_AD_SCORE_ = '_ZHUAN_USER_FIRST_AD_SCORE_'

#     @staticmethod
#     def reconn():
#         _REDIS = redis.Redis(host=options.redis_host,
#                      port=options.redis_port,
#                      db=options.redis_db)
    @staticmethod
    def get_instance(host_name=''):
        pool_num = random.randint(0,_REDIS_CONN_NUM-1)
        if not host_name:
#             print _REDIS[pool_num]
#             print sys.getsizeof( _REDIS[pool_num])
            return _REDIS[pool_num]
        else:
            return _REDIS_HOST_LIST[host_name][pool_num]
            
