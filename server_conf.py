# -*- coding: UTF-8 -*-
from tornado.options import define,options as _options
# import logging
import os,re

define('root_path', default='/opt/spzhuan/api', help='invite pkg path')
define('package_path', default='/opt/spzhuan/api/html/pkg/', help='invite pkg path')
define("package_domain", default="sohu-cdn.dianjoy.com", help="package request domain")
define('port', default=9819, help='this server will listen on the port')
define('process', default=16, help='work process')
define('debug', default=False, help='is in debug mode?')
define('appid', default="c81bc556d5dc52b854f591320d4c951b", help='is in debug mode?')
define('iosappid', default="5763c2eb596b7a4e511f588d4ee7e50f", help='is in debug mode?')

define("db_host", default="", help="db_host")
define("db_port", default="", help="db_port")
define("db_uname", default="", help="db_uname")
define("db_upass", default="", help="db_upass")
define("db_name", default="", help="db_name")

define("db_host_name_list", default="", help="db_host")

#添加redis服务器需要先填写名称，用“,”隔开
define('redis_host_name_list',default='', help='host list of redis server')
#添加redis服务器需要添加3项内容，中间填写名称，用“_”和其他默认部分连接
define('redis_host', default='', help='host of redis server')
define('redis_port', default=6379, help='port number of redis')
define('redis_db', default=6, help='db base number of redis')

define("db_max_process", default=2000, help="max db process num")
define("func_max_process", default=10000, help="max func process num")


define('APP_VERSION', default='1.1.1', help='app version for update') # 用户端提示更新改这个
define('APP_VERSION_DEL', default='1', help='app version for delelop')
define('PAK_VERSION', default='1.3.2.5', help='package show version') # 打渠道包修改这个
define('PAK_VERSION_CHANNEL', default='1.3.2.5', help='package jump version') # 渠道包跳转修改这个
# 默认的下载地址  这个需要舜东传到CDN
define('APP_NEW_APK', default='http://fast-cdn.dianjoy.com/dev/upload/ad_url/hongbao/hongbaosuoping.apk', help='app version apk for update')
define('IOS_APP_NEW_APK', default='itms-services://?action=download-manifest&url=https://www.hongbaosuoping.com/plist/update.plist', help='ios_app version apk for update')
# define('IOS_APP_NEW_APK', default='itms-services://?action=download-manifest&url=https://www.hongbaosuoping.com/plist/share.plist', help='ios_app version apk for update')

_LOCAL_PATH_ = os.path.abspath(os.path.dirname(__file__))
_CONF_PATH_ = os.path.join(_LOCAL_PATH_, "server.conf")
try:
    _options.parse_config_file(_CONF_PATH_)
except:
    print 'load server.conf failed , use command line option'
#     logging.error('load server.conf failed , use command line option')
    
def creat_db_define(db_tag):
    define("db_"+db_tag+"_host", default="", help="db_host")
    define("db_"+db_tag+"_port", default="", help="db_port")
    define("db_"+db_tag+"_uname", default="", help="db_uname")
    define("db_"+db_tag+"_upass", default="", help="db_upass")
    define("db_"+db_tag+"_name", default="", help="db_name")

# 通过第一次加载的配置项再增加数据库等配置项，这种情况需要再加载一遍，因为tornado必须在这里定于
for db_tag in _options.db_host_name_list.split(","):
    special_tag = re.findall("\[(.+)\]", db_tag)
    if special_tag:
        special_tag = special_tag[0]
        db_tag = db_tag.replace(re.findall("(\[.+\])", db_tag)[0],"")
        db_tag_arr = []
        analyse_num_tag = re.findall("([0-9]+)\-([0-9]+)", special_tag)
        if analyse_num_tag:
            db_tag_arr = [ x for x in range(int(analyse_num_tag[0][0]),int(analyse_num_tag[0][1])+1) ]
            special_tag = special_tag.replace(re.findall("([0-9]+\-[0-9]+)", special_tag)[0],"")
        if len(special_tag) > 0:
            for x in special_tag:
                db_tag_arr.append(x)
        if db_tag_arr:
            for db_sub_tag in db_tag_arr:
                creat_db_define(db_tag+str(db_sub_tag))
    else:
        creat_db_define(db_tag)

for db_tag in _options.redis_host_name_list.split(","):
    define("redis_"+db_tag+"_host", default="", help="db_host")
    define("redis_"+db_tag+"_port", default=6379, help="db_port")
    define("redis_"+db_tag+"_db", default=1, help="db_uname")

# 通过二次加载解决无法增加不存在配置项问题
try:
    _options.parse_config_file(_CONF_PATH_)
except:
#     logging.error('second load server.conf failed , use command line option')
    print 'second load server.conf failed , use command line option'

