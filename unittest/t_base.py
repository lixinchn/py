# -*- coding: UTF-8 -*-
# author: lixin
import traceback
import thrift,urllib,time
from thrift.transport.TTransport import TTransportException
from thrift.transport import TTransport
from thrift.transport import TSocket
from thrift.transport import TSSLSocket
from thrift.transport import THttpClient
from thrift.protocol import TBinaryProtocol
import sys
sys.path.append('..')
from user_service import UserService
from user_service.ttypes import *


class BaseService(object):
    '''
    classdocs
    '''
    transport = None
    client = None
    
    def __init__(self):
        '''
        Constructor
        '''
        #print self.__class__.__name__
        self.get_conn()
    
    def get_conn(self):
        if self.transport == None:
            self.socket = TSocket.TSocket("localhost", 9091)
#            self.socket = TSocket.TSocket("192.168.199.8", 9091)       # 测试环境
#            self.socket = TSocket.TSocket("192.168.99.212", 9091)      # 预生产
#           self.socket = TSocket.TSocket("192.168.99.164", 9094)       # 生产
#           self.socket = TSocket.TSocket("192.168.99.234", 9095)
            self.socket.setTimeout(5000) #time out 10 sec
            self.transport = TTransport.TBufferedTransport(self.socket)
            protocol = TBinaryProtocol.TBinaryProtocol(self.transport)
#           protocol = TJSONProtocol.TSimpleJSONProtocol(self.transport)
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
