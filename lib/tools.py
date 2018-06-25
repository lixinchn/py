# _*_encoding:utf-8_*_
# 解决源文件不兼容中文的问题
import re 

def check_IMEI(imei):
    i=0
    sum1=0
    sum2=0
    total=0
    temp=0
    for i in range(0,14):
        if i%2 ==0:
            sum1 = sum1 +int( imei[i],16)
        else:
            temp = (int(imei[i],16))*2
            if temp<10:
                sum2=sum2+temp
            else:
                sum2 = sum2 + 1 + temp - 10
    total = sum1+sum2
    if total%10 == 0:
        return '0'
    else:
        return str((((total/10) * 10) + 10 - total)) #python中total/10等于是取total的10位数，这个写法在其他很多语言中都会得到小数，要小心

def if_IMEI_valid(imei):
    if len(imei) != 15:
        return True
    if len(imei)==15 and imei[14]!=check_IMEI(imei):
        return False
    return True