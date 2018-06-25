# -*- coding: UTF-8 -*-

import re,datetime
from ttypes import InvalidOperation,Errtype,UserTicket,Apptype
from lib.redis_manager import m_redis
from lib.tools import if_IMEI_valid

class BaseHandle():
    AllowIp = ["127.0.0.1"]
    remoteAddress = ""
    def checkIp(self):
        if not self.remoteAddress == "" and self.remoteAddress in self.AllowIp:
            return True
        return False
    
    def _validate_param(self,param_name,param_value):
        if not param_value:
                raise  InvalidOperation(Errtype.PARAM_NOT_ALLOW_EMPTY,"参数%s不能为空。"%param_name)
        
        
        if param_name == "pnum":
            if not re.match(r"\d{11}", str(param_value)):
                raise  InvalidOperation(Errtype.PNUM_FORMATE_WRONG,"手机号格式错误。")
            return True
        if param_name == "uid":
            if not re.match(r"\d{8,10}", str(param_value)):
                raise  InvalidOperation(Errtype.UID_FORMATE_WRONG,"uid格式错误。")
            return True
        if param_name == "os_type":
            if not re.match(r"android|ios", str(param_value)):
                raise  InvalidOperation(Errtype.OS_FORMATE_WRONG,"os_type格式错误。")
            return True
        if param_name == "app_id":
            if not Apptype._VALUES_TO_NAMES.has_key(int(param_value)):
                raise  InvalidOperation(Errtype.APP_ID_FORMATE_WRONG,"app_id输入错误。")
            return True
        if param_name == "device_id":
            d_len = len(param_value)
            if re.match(r"emulator", str(param_value)) or (d_len not in [36,14,15] ):
                raise  InvalidOperation(Errtype.DEVICE_ID_FORMATE_WRONG,"设备无法识别。")
            # 15位全是数字 前14验证最后1位  14 a开头
#             if d_len == 14 and not re.match(r"^a", str(param_value)):
#                 raise  InvalidOperation(Errtype.DEVICE_ID_FORMATE_WRONG,"设备无法识别。")
#             try:
#                 if not if_IMEI_valid(param_value):
#                     raise  InvalidOperation(Errtype.DEVICE_ID_FORMATE_WRONG,"设备无法识别。")
#             except:
#                 raise  InvalidOperation(Errtype.DEVICE_ID_FORMATE_WRONG,"设备无法识别。")
            
            return True
    

    #计数器功能
    #只适用于累计不跨天的计数
    #尽量不用这个
    #增加月份 onmonth
    def get_counting(self,key,interval,default_cooltime=1,onmonth=0):
        today = str(datetime.date.today()) if not onmonth else str(datetime.date.today())[:7]
        r_cool_key = "service_"+key+"_"+today
        r = m_redis.get_instance()
        rcooltime = r.incr(r_cool_key)
        if rcooltime == 1: r.expire(r_cool_key,interval)
        if default_cooltime != 1:
            if rcooltime > default_cooltime :
                return True
        elif rcooltime != 1 :
            return True
        return False

        
