# -*- coding: UTF-8 -*-
#!/usr/bin/env python2.7
# thrift --gen py helloworld.thrift

import sys
from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from thrift.protocol import TCompactProtocol
from thrift.server import TServer
from tornado.options import define,options as _options
import server_conf

from user_service import UserService
from user_service.service_enter import ServiceHandle

DAEMON="hongbao_service"
try:
    import setproctitle
except ImportError:
    pass
else:
    setproctitle.setproctitle(DAEMON)

# import logging
# logging.basicConfig(level=logging.DEBUG)
# logging.debug("log info")

#取得IP需要重写下面两个方法   取得socket的信息   并间接传递

class TBTFactory(TTransport.TBufferedTransportFactory):

    def getTransport(self, trans):
        # trans.handle is socket object
#         print dir(trans.handle)
#         print trans.handle.getsockname()
#         print trans.handle.getpeername()
        (remoteAddress,port) = trans.handle.getpeername()
        ttrans = TTransport.TBufferedTransportFactory.getTransport(self,trans)
        ttrans.remoteAddress = remoteAddress
        return ttrans

#         trans.remoteAddress = self.remoteAddress
#         return trans

class SuperProcessor(UserService.Processor):
    
    def process(self, iprot, oprot):
        self._handler.remoteAddress = iprot.trans.remoteAddress
#         iprot.trans.remoteAddress = None
        return UserService.Processor.process(self, iprot, oprot)

port = 9091
if len(sys.argv) >1:
    port = sys.argv[1]
    
handler = ServiceHandle()
# 已升级可取得clinet ip
# processor = UserService.Processor(handler)
processor = SuperProcessor(handler)
transport = TSocket.TServerSocket('0.0.0.0',port)
# tfactory = TTransport.TBufferedTransportFactory()
tfactory = TBTFactory()
pfactory = TBinaryProtocol.TBinaryProtocolFactory()
server = TServer.TThreadedServer(processor, transport, tfactory, pfactory)
# server = TServer.TThreadPoolServer(processor, transport, tfactory, pfactory)
# server.setNumThreads(10)

print "Starting python %s server... "%port
server.serve()
print "done!"    
