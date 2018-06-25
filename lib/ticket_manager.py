# -*- coding: UTF-8 -*-

import StringIO, base64
from M2Crypto import EVP
from M2Crypto import RC4
import time

_testing = False

_myticket_bf_key = "183*%^#$@!376)(&"
_myticket_iv = '\xdc\x23gT#\xef\x11\xab'
_myticket_pw_md5_key = ''
_myticket_expire_time = 31536000 #365天

def blowfish_encrypt(s, op = 0):
    out=StringIO.StringIO()
    m=EVP.Cipher("bf_cbc", _myticket_bf_key, _myticket_iv, op, padding = 1)
    out.write(m.update(s))
    out.write(m.final())
    return out.getvalue()


def ticket_encode(data):
    ticket = blowfish_encrypt(data, 1)
    return base64.urlsafe_b64encode(ticket)

def ticket_decode(ticket):
    ticket = base64.urlsafe_b64decode(ticket)
    return blowfish_encrypt(ticket)



def create_ticket(uid,device_id,pw):
    if not uid or not device_id or not pw:
        return ""
    
    str = "%s:%s:%s:%s"%(uid,device_id,pw,int(time.time()))
    #thrift  真心蛋疼啊  非得转码  日
    str = str.decode("utf8").encode("latin1")
    return ticket_encode(str)

def explain_ticket(ticket):
    str = ticket_decode(ticket)
    (uid,device_id,pw,gen_time)=str.split(":")
    if int(time.time()) < int(gen_time)+_myticket_expire_time:
        return (uid,device_id,pw,gen_time)
    return (None,None,None,None)


if __name__ == "__main__":
    d = create_ticket(67388840, '863151020303575', '717e58fbac8ae54936b78e3b9d2961a3')
#     d = create_ticket(67388840, '863151020303575', '717e58fbac8ae54936b78e3b9d2961a3')
    print d
    print explain_ticket(d)
#     print explain_ticket('MfH9SMgFiZFohF7kigtIxCHiORbcVKoQWgTBHthZ1mbh92qnI22AN1SOUmb6ZjWZJTCVk3ArhMB5GlnhBdVrol1dEa57wdlxKDgzfhto8XAz_Zm126IPyznIImvezF5otBBqF1rsReb9HYBNetAMC8T1CbwU5PzlVwzGXtRnU1J5kut-h51L7QtQN3VXTdk_')





