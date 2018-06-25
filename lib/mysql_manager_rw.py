# -*- coding: UTF-8 -*-
"""
mysql连接管理类
只能在tornado里面用

主要目标：
带读写分离，带多读库支持

次要目标：
带任何条件下数据库异步

@author: zh
"""
import MySQLdb,traceback
from tornado.options import define, options as _options
import MySQLdb.cursors

from DBUtils.PooledDB import PooledDB

_POOLED_DB = {}

class MysqlConn:
#     executor = ThreadPoolExecutor(_options.db_max_process)
    db = None
    cur = None
    default_db_name = ""
    default_charset = "utf8"

    def __init__(self, db_name=""):
        self.default_db_name = db_name

    def get_conn(self):
        
        if self.db:
            return

        # 主库 读写

        if not self.default_db_name and not _POOLED_DB.has_key("_default"):
            conn_args = {"host":_options.db_host, 
                          "user":_options.db_uname,
                          "passwd":_options.db_upass, 
                          "port":int(_options.db_port),
                          "db":_options.db_name,
                          "charset":self.default_charset,
                          "cursorclass":MySQLdb.cursors.DictCursor }
            
            _POOLED_DB["_default"] = PooledDB(MySQLdb,mincached=5, maxcached=20, blocking=True, maxshared=0, maxusage=10000,**conn_args)
        
        # 其他各种库
        if self.default_db_name and not _POOLED_DB.has_key(self.default_db_name):     
            conn_args = {"host":getattr(_options, "db_" + self.default_db_name + "_host"), 
                          "user":getattr(_options, "db_" + self.default_db_name + "_uname"),
                          "passwd":getattr(_options, "db_" + self.default_db_name + "_upass"), 
                          "port":int(getattr(_options, "db_" + self.default_db_name + "_port")),
                          "db":getattr(_options, "db_" + self.default_db_name + "_name"),
                          "charset":self.default_charset,
                          "cursorclass":MySQLdb.cursors.DictCursor }
            
                
            _POOLED_DB[ self.default_db_name ] = PooledDB(MySQLdb,mincached=5, maxcached=20, blocking=True, maxshared=0, maxusage=10000,**conn_args)
        
        if not self.default_db_name:
            self.db = _POOLED_DB["_default"].connection()
        else:
            self.db = _POOLED_DB[self.default_db_name].connection()
#         self.db.autocommit(1)
        self.cur = self.db.cursor()
        
            
        


    @staticmethod
    def F(sql):

        sql = MySQLdb.escape_string(sql)
        return sql


    # 异步方式请求数据库
#     @run_on_executor
    def SQ(self, sql):
        return self._query(sql)

    # 普通方式请求数据库
    def Q(self, sql):
        return self._query(sql)


    def _query(self, sql):

        try:
            self.get_conn()
#             self.db.autocommit(True)
            rs = self.cur.execute(sql)
            self.db.commit()
            return rs
        except MySQLdb.Error, e:
            traceback.print_exc()
            print "_query error: %s" % sql
#             logging.error("_query error: %s" % sql)

    def fetchone(self):
        return self.cur.fetchone()

    def fetchall(self):
        return self.cur.fetchall()

    def close(self):
        try:
            self.cur.close()
        except:
            pass
        finally:
            self.cur = None
        try:
            self.db.close()
        except:
            pass
        finally:
            self.db = None

    def __del__(self):
        try:
            if self.db != None:
                self.close()
        except:
            pass
