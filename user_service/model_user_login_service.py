# -*- coding: UTF-8 -*-
'''
Created on 2015年3月5日

@author: lixin
'''
from ttypes import InvalidOperation,UserAddObj
from ttypes import UserInfo as UInfo,Errtype,UserTicket,InvalidOperation
import urllib,traceback,json,datetime,time,math,re,random,hashlib
from lib.mysql_manager_rw import MysqlConn as mmysql
from lib.redis_manager import m_redis
from user_service.model_score_service import ScoreServiceHandle
from lib.json_manager import CJsonEncoder
from lib import ticket_manager
from base import BaseHandle


class UserLoginServiceHandle(BaseHandle):
    def get_pnum(self, pnum):
        return hashlib.md5(str(pnum) + 'dianABCDE5').hexdigest()
    
    def registerUser(self, userobj):
        self._validate_param("pnum", userobj.pnum)
        self._validate_param("password", userobj.pw)
        self._validate_param("device_id", userobj.device_id)
        self._validate_param("os_type", userobj.os_type)
        self._validate_param("client_ip", userobj.client_ip)

        if self.get_counting("regiester_dont_repeat" + str(userobj.pnum), 10):
            raise  InvalidOperation(Errtype.REQUEST_TOO_FASTER, "相同pnum访问过快，或访问异常。")
        if self.getUidByPnum(userobj.pnum):
            raise  InvalidOperation(Errtype.USER_IS_EXIST, "用户已经存在。")
        if self.getUidByDeviceId(userobj.device_id):
            raise  InvalidOperation(Errtype.DEVICE_ID_IS_EXIST, "设备已经存在。")
        
        invite_code = 0
        if re.match(r"^\d{8,10}$", str(userobj.ic)):
            invite_code = userobj.ic
        if userobj.ic and re.match(r"^\d{11}$", str(userobj.ic)):
            invite_code = self.getUidByPnum(userobj.ic) or 0

        try:
            uid = self.addUser(UserAddObj(int(userobj.pnum), userobj.pw, userobj.device_id, userobj.imsi, str(invite_code), userobj.os_type, userobj.channel, userobj.client_ip, userobj.app_id))
        except:
            raise InvalidOperation(Errtype.SYSTEM_WRONG, traceback.format_exc())
            
        if not uid:
            raise  InvalidOperation(Errtype.SYSTEM_WRONG, "系统错误，添加失败。")
        
        return uid
    
    def userLogin(self, pnum, pw, device_id, os_type, client_ip, app_id,imsi = '', channel = ''):
        self._validate_param("pnum", pnum)
        self._validate_param("password", pw)
        self._validate_param("device_id", device_id)
        
        # 2 秒防爆破
        r = m_redis.get_instance()
        no_boom_key = "userLogin_" + str(pnum)
        no_boom_val = r.get(no_boom_key)
        if no_boom_val:
            if no_boom_val == "null":
                raise  InvalidOperation(Errtype.REQUEST_TOO_FASTER, "访问过快，或访问异常。")
            else:
                return UserTicket(True, no_boom_val)
        r.set(no_boom_key, "null", 2)
        userinfo = self.getUserInfo(pnum, client_ip, 0, app_id)
        if not userinfo or not userinfo.uid:
            raise  InvalidOperation(Errtype.USER_NO_FIND, "抱歉，账户不存在。")
        if self._get_password(pw) != userinfo.pword:
            raise  InvalidOperation(Errtype.PASSWORD_WRONG, "密码错误。")
    
        # 判断是否已经在 app register 里面注册了  如果没有 注册进去
        is_app_register = self.existAppRegister(int(userinfo.uid), app_id)
        if not is_app_register:
            try:
                if not self.addAppRegister(int(userinfo.uid), 0, device_id, imsi, os_type, channel, client_ip):
                    raise  InvalidOperation(Errtype.DEVICE_ID_NOT_BIND, "抱歉，您已被其他账号绑定。")
            except:
                raise  InvalidOperation(Errtype.DEVICE_ID_NOT_BIND, "抱歉，您已被其他账号绑定。")

        ticket = ticket_manager.create_ticket(userinfo.uid, userinfo.device_id, userinfo.pword)
        if ticket:
            r.set(no_boom_key,ticket, 10)
            return UserTicket(True, ticket)
        else:
            raise  InvalidOperation(Errtype.TICKET_CREATE_FAILD, "ticket 生成失败！")
        
    def getTicket(self, uid, device_id, pword):
        ticket = ticket_manager.create_ticket(uid, device_id, pword)
        if ticket:
            return UserTicket(True, ticket)
        else:
            raise  InvalidOperation(Errtype.TICKET_CREATE_FAILD, "ticket 生成失败！")
    
    def validateUserToken(self, token, app_id):
        self._validate_param("token", token)
        
        try:
            (uid, device_id, pw, gen_time) = ticket_manager.explain_ticket(token)
        except:
            raise InvalidOperation(Errtype.TICKET_EXPLAIN_FAILD, "ticket 解析失败,或失效！")
        
        if not uid:
            raise InvalidOperation(Errtype.TICKET_EXPLAIN_FAILD, "验证未通过或ticket失效！")
        
        try:
            user_info = self.getUserInfoByUid(uid, app_id = app_id)
            if not user_info or not user_info.uid:
                raise InvalidOperation(Errtype.USER_NO_FIND, "抱歉，账户不存在！")
        except:
            raise InvalidOperation(Errtype.USER_NO_FIND, "抱歉，账户不存在！")
        
        if user_info.pword != pw:
            raise  InvalidOperation(Errtype.USER_NOT_VALIDATE, "ticket密码错误！")
        
        return user_info
        
        

        
        
        
        
        