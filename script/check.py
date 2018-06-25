# -*- coding: UTF-8 -*-
'''
Created on 2015年3月19日

@author: zh
'''

import sys,os,math,traceback,datetime,time

DAEMON="hongbao_import_user"
try:
    import setproctitle
except ImportError:
    pass
else:
    setproctitle.setproctitle(DAEMON)

_LOCAL_PATH_ = os.path.abspath(os.path.dirname(__file__))
modules_folder = os.path.abspath(_LOCAL_PATH_+'/..')
if modules_folder not in sys.path:
    sys.path.append(modules_folder)   
modules_folder = os.path.abspath(_LOCAL_PATH_+'/../lib')
if modules_folder not in sys.path:
    sys.path.append(modules_folder)
# modules_folder = os.path.abspath(_LOCAL_PATH_+'/../applib')
# if modules_folder not in sys.path:
#     sys.path.append(modules_folder)

from tornado.options import define,options as _options
import server_conf

from lib.mysql_manager_rw import MysqlConn


import sys
if __name__ == '__main__':
    

    mm = MysqlConn("old_hongbao")
    sql =''' SELECT SUM(score) AS num,SUM(score_ad) AS score_ad,SUM(score_right_catch) AS score_right_catch,
            SUM(score_register) AS score_register,SUM(score_other) AS score_other,SUM(score_task) AS score_task FROM z_user'''
    mm.Q(sql)
    one = mm.fetchone()
    print "old:%s %s %s %s %s %s "%(one["num"],one["score_other"],one["score_task"],one["score_register"],one["score_right_catch"],one["score_ad"])
    mm.close()
    
    
    
    
    
    
    
    
    
    
    
    
    
    