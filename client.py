# -*- coding: UTF-8 -*-
'''
Created on 2015年3月9日

@author: zh
'''
import traceback
import thrift,urllib,time
from thrift.transport.TTransport import TTransportException
from thrift.transport import TTransport
from thrift.transport import TSocket
from thrift.transport import TSSLSocket
from thrift.transport import THttpClient
from thrift.protocol import TBinaryProtocol


from user_service import UserService
from user_service.ttypes import *


class BaseSevice(object):
    '''
    classdocs
    '''
    transport = None
    client = None
    
    def __init__(self):
        '''
        Constructor
        '''
        print self.__class__.__name__
        self.get_conn()
    
    def get_conn(self):
        if self.transport == None:
#             self.socket = TSocket.TSocket("localhost", 9091)
            self.socket = TSocket.TSocket("192.168.199.8", 9091)
#             self.socket = TSocket.TSocket("192.168.99.212", 9091)
#             self.socket = TSocket.TSocket("192.168.99.164", 9094)
#             self.socket = TSocket.TSocket("192.168.99.234", 9095)
            self.socket.setTimeout(5000) #time out 10 sec
            self.transport = TTransport.TBufferedTransport(self.socket)
            protocol = TBinaryProtocol.TBinaryProtocol(self.transport)
#             protocol = TJSONProtocol.TSimpleJSONProtocol(self.transport)
            self.client = UserService.Client(protocol)
            self.transport.open()
        
    def close(self):

        try:
            
#             self.socket.close()
            self.transport.close()
        except:
            pass


    def __del__(self):
        try:
            if self.transport != None:
                self.close()
        except:
            pass
        
"""
UserAddObj: UserAddObj(client_ip='127.0.0.1',
 vc='12334', pnum=18600432855L, 
 pw=u'eewwefasfdsf', app_id=1, 
 channel='wall_1350', 
 ic='', 
 app_version='0.0.0.0',
  os_type='android', 
  imsi='460025012436898', device_id='863151020303571')
  现在是16m
"""       


sa = ScoreAddObj(client_ip='127.0.0.1', trade_type=0, uid=71159353, order_id='0', app_id=1, currency=1500, pack_name='com.happy.lock.wifi', action_type=8, ad_name='数据库被删了，做测试用的', time_stamp=120, device_id='863151020303571')
# user = UserAddObj(18123456789,"wwwwwww","vvvvvvvv","kkk","123645678","ios","test","1.1.1.1",0)
# user = UserAddObj(client_ip='127.0.0.1', pnum=18600432852L, pw=u'123456', app_id=1, channel='wall_1350', os_type='android', ic='', imsi='460036090242703', device_id='made00000443a4731')
user_ex = UserExInfo(uid=12345678,sex=1,birthday='2015-05-14',workspace=1)
for i in range(10000):
    
    t = time.time()
#     b = None
    b=BaseSevice()
    try:
        print b.client.getUserExInfo(71173651)
#         print b.client.createUserExInfo(user_ex)
#         print b.client.getInviteMember(20197239)
#         print b.client.updateUserPoint(12345678,60,30)
#         print b.client.ping("")
#         print b.client.ping("")
#         print b.client.ping("")
#         time.sleep(10)
#         print b.client.getUserInfo(18601150311, "", 0, 0)
#         print b.client.getUserInfoByUid(92441788, "", 0, 0)
#         print b.client.getUserPointById(86486618)
#         print b.client.getUserTodayScoreList(80710132,True)
#         print b.client.updateUserPoint(12345678,60,30)
#         print b.client.getUserPointById(12345678)
#         print b.client.getUserScoreList(80561993)
#         print b.client.existUser(82485056)
    except:
        traceback.print_exc()
    # print b.client.addUser(user)
    # try:
    #     print b.client.ping("")
    # except InvalidOperation , io:
    #     print io.why
    
    # print b.client.getUserScoreList(78405303)
    # print b.client.delUser( 13717528295 )
    
    #     ad_name = '%s_%s'%("com.kingyee.kymh",unicode(urllib.unquote("%E6%8E%A8%E4%BA%8B%E6%9C%AC-%E4%BC%81%E4%B8%9A%E7%89%88")).encode("utf8"))
    #     print b.client.ping(ad_name)
    #     print b.client.ping("ios签到")
    #     print b.client.getUserInfoByUid(12345678,"",0,0)
    #     print b.client.updateUserPassword("123456",12345678,18601150314)
    #     print b.client.getUserInfoByUid(12345678,"",0,0)
    
#     print b.client.getUserInfo(18601150311, "", 0, 0)
    
    # print b.client.updateUserDeviceId(94785422,"E29892EE-91DF-4B9B-9FB3-B388922C4310","1234566",app_id=0)
    # print b.client.getUserInfo(13488815121, "", 0, 0)
    # print b.client.updateUserDeviceId(94785422,"1234566","E29892EE-91DF-4B9B-9FB3-B388922C4310",app_id=0)
    # print b.client.getUserInfo(13488815121, "", 0, 0)
    
    #     print b.client.getUserInfo(18601150311, '192.168.198.240', 1,0)
    # 
        # print ua
#     user = b.client.addScore(sa)
    # print user
    #     rs = b.client.getUserScoreList(12345678)
    # rs = b.client.getUserTodayScoreList(71159353)
    # rs = b.client.userLogin(18600432859,"eewwefasfdsf","863151020303575","android","1.1.1.1",1,"","")
    # print rs.ticket
    # print b.client.validateUserToken(rs.ticket,1)
    # print rs
    if b:
        b.close()
    print i
    print time.time() - t



