# -*- coding: UTF-8 -*-
'''
Created on 2015年3月13日

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

# step = 10.0
step = 10000.0

def getOldUser(page , update_time=""):
    m = MysqlConn()
    sql = "select * from z_user where 1 %s order by update_time desc limit %s,%s"%(update_time,int(page*step),int(step))
    m.Q(sql)
    rs = m.fetchall()
    m.close()
    return rs


def insertNewLine(update_time_sql):
#     update_time_sql = ""
    m = MysqlConn()
    sql = "select count(*) as num from z_user where 1 %s"%(update_time_sql)
    print sql
    m.Q(sql)
    rs = m.fetchone()
    m.close()
    countpage = math.ceil(int(rs["num"])/step)
    print countpage
    try:
        for page in range(0,int(countpage)):
            print "%s / %s"%(page,countpage)
            rs = getOldUser( page ,update_time_sql)

            z_app_str = "update app_register_%s set device_id='%s',imsi='%s',os_type='%s',channel='%s',register_ip='%s' where uid=%s and appid=0;"
            z_app_values = []
            
    
            for line in rs:
                uid = line["uid"]

                z_app_values.append(z_app_str%(str(uid)[-1],line["device_id"],line["imsi"],line["os_type"],line["channel"],line["register_ip"],uid))
                

            
#             print "".join(z_app_values)
            #app注册表
            mm = MysqlConn()
            mm.Q("".join(z_app_values))
            mm.close()
            del z_app_values
            

    except:
        print traceback.format_exc()
        exit()


import sys
if __name__ == '__main__':
    

    insertNewLine(" and ctime < '2015-03-24 16:10:00' ")

        




    
    
    
    
    
    
    