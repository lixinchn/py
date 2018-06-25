# -*- coding: UTF-8 -*-
'''
Created on 2015年3月19日

@author: zh
'''
exit()
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
    
    all_score = 0
    score_other=0
    score_task=0
    score_register=0
    score_right_catch=0
    score_ad = 0
    for i in range(10):
        mm = MysqlConn("score_%s"%i)
        for x in range(10):
            sql =''' SELECT SUM(score) AS num,SUM(score_ad) AS score_ad,SUM(score_right_catch) AS score_right_catch,
            SUM(score_register) AS score_register,SUM(score_other) AS score_other,SUM(score_task) AS score_task 
             FROM z_user_score_%s'''%x
            mm.Q(sql)
            one = mm.fetchone()
            all_score+= int(one["num"])
            score_other+= int(one["score_other"])
            score_task+= int(one["score_task"])
            score_register+= int(one["score_register"])
            score_right_catch+= int(one["score_right_catch"])
            score_ad += int(one["score_ad"])
        mm.close()
    print "new:%s %s %s %s %s %s "%(all_score,score_other,score_task,score_register,score_right_catch,score_ad)
        
    
    mm = MysqlConn("hongbao_user_source")
    sql =''' SELECT SUM(score) AS num,SUM(score_ad) AS score_ad,SUM(score_right_catch) AS score_right_catch,
            SUM(score_register) AS score_register,SUM(score_other) AS score_other,SUM(score_task) AS score_task FROM z_user'''
    mm.Q(sql)
    one = mm.fetchone()
    print "old:%s %s %s %s %s %s "%(one["num"],one["score_other"],one["score_task"],one["score_register"],one["score_right_catch"],one["score_ad"])
    mm.close()
    
    
    
    
    
    
    
    
    
    
    
    
    
    