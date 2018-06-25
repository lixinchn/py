# -*- coding: UTF-8 -*-
'''
Created on 2015年3月13日

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

# step = 10000.0
step = 5000.0

def getOldUser(page , update_time=""):
    m = MysqlConn("hongbao_user_source")
    sql = "select * from z_user where 1 %s order by update_time desc limit %s,%s"%(update_time,int(page*step),int(step))
    print sql
    m.Q(sql)
    rs = m.fetchall()
    m.close()
    return rs


def insertNewLine(update_time_sql):
#     update_time_sql = ""
    m = MysqlConn("hongbao_user_source")
    sql = "select count(*) as num from z_user where 1 %s"%(update_time_sql)
    m.Q(sql)
    rs = m.fetchone()
    m.close()
    countpage = math.ceil(int(rs["num"])/step)

    try:
        for page in range(0,int(countpage)):
            print page
            rs = getOldUser( page ,update_time_sql)
            z_user_str = "insert into z_user(uid,pnum,pnum_md5,password,status,device_id,imsi,os_type,ctime,register_ip,invite_code,channel,ulevel,update_time) values"
            z_user_values = []
            
            z_app_str = "insert into app_register_%s(uid,appid,rtime) values"
            z_app_values = []
            
            z_score_str = "insert into z_user_score_%s(uid,score,update_time,score_ad,score_right_catch,score_register,score_other,score_task) values"
            z_score_values = {}
            for x in range(10):
                z_score_values[str(x)]=[]
    
            for line in rs:
                uid = line["uid"]
                update_time = line["update_time"].strftime('%Y-%m-%d %H:%M:%S')
                ctime = line["ctime"].strftime('%Y-%m-%d %H:%M:%S')
                z_user_values.append(z_user_str + "('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s') ON DUPLICATE KEY UPDATE device_id='%s' ;"% \
                (line["uid"],line["pnum"],line["pnum_md5"],line["password"],line["status"],line["device_id"],line["imsi"],line["os_type"],ctime,line["register_ip"],line["invite_code"],line["channel"],line["ulevel"],update_time,line["device_id"])
                )
                
                z_app_values.append(z_app_str%str(uid)[-1] + "('%s','%s','%s') ON DUPLICATE KEY UPDATE rtime='%s' ;"%(line["uid"],0,ctime,ctime)
                                    )
                
                z_score_values[str(uid)[-2]].append(
                z_score_str%str(uid)[-1] + "('%s','%s','%s','%s','%s','%s','%s','%s') ON DUPLICATE KEY UPDATE score='%s',update_time='%s',score_ad='%s',score_right_catch='%s',score_register='%s',score_other='%s',score_task='%s' ;"% \
                (line["uid"],line["score"],update_time,line["score_ad"],line["score_right_catch"],line["score_register"],line["score_other"],line["score_task"],line["score"],update_time,line["score_ad"],line["score_right_catch"],line["score_register"],line["score_other"],line["score_task"])
                )
            
            #完成用户表插入
            mm = MysqlConn()
            mm.Q("".join(z_user_values))
            mm.close()
            del z_user_values
            z_user_values = []
            #app注册表
            mm = MysqlConn()
            mm.Q("".join(z_app_values))
            mm.close()
            del z_app_values
            
            
            for dbn in z_score_values.keys():
                if not z_score_values.get(dbn):
                    continue
                mm = MysqlConn("score_%s"%dbn)
                mm.Q("".join(z_score_values.get(dbn)))
                mm.close()
            del z_score_values
    except:
        print traceback.format_exc()
        exit()


import sys
if __name__ == '__main__':
    

    insertNewLine("and update_time >='2015-03-19 01:00:00' and update_time <= now() ")

        




    
    
    
    
    
    
    