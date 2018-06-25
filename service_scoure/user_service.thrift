
/**
 * @author: zh
 * 
 */

#include "public.thrift"

exception InvalidOperation {
	1: i32 what,
	2: string why
}

#异常类型
enum Errtype {

	# 基础错误
	TICKET_CREATE_FAILD = 90001,
	TICKET_EXPLAIN_FAILD = 90002,
	REQUEST_TOO_FASTER = 90003,
	SYSTEM_WRONG = 90004,
	
	# 逻辑错误
	USER_NO_FIND = 10020,
	USER_NOT_VALIDATE = 10015,
	USER_IS_EXIST = 10032,
	PASSWORD_WRONG = 10021,
	DEVICE_ID_NOT_BIND = 10031,
	DEVICE_ID_IS_EXIST = 10033,
	
	PARAM_NOT_ALLOW_EMPTY = 20001,
	PNUM_FORMATE_WRONG = 20101,
	UID_FORMATE_WRONG = 20102,
	OS_FORMATE_WRONG = 20103,
	APP_ID_FORMATE_WRONG = 20104,
	DEVICE_ID_FORMATE_WRONG = 20105,
}

struct UserAddObj {
	1:i64 pnum,
	2:string pw,
	3:string device_id,
	4:string imsi,
	5:string ic,
	6:string os_type,
	7:string channel,
	8:string client_ip,
	9:i32 app_id,
	10:optional string app_version='',
}

# 加分类型
enum Scoretype {
	_ACTION_TYPE_AD = 0, 				# 广告回调加分
	_ACTION_TYPE_RIGHT_CATCH = 1, 		# 锁屏右划加分
	_ACTION_TYPE_REGISTER = 2, 			# 注册邀请加分
	_ACTION_TYPE_OTHER = 3, 			# 类型不明加分
	_ACTION_TYPE_TASK = 4, 				# 任务加分
	_ACTION_TYPE_ACTIVE = 5, 			# 活动加分
	_ACTION_TYPE_SCORE_REDUCE = 6, 		# 因兑换等动作余额减少
	_ACTION_TYPE_SCORE_REFUND = 7, 		# 因无法支付等原因造成的退款 这种是不显示变动的但是会记录 log
	_ACTION_TYPE_WIFI_SHARED = 8, 		# 分享 wifi 加分
	_ACTION_TYPE_BIND_BANK_CARD = 9,	# 绑卡广告加分
	_ACTION_TYPE_AD_WALL_20 = 10,		# 积分墙 2.0 加分
	_ACTION_TYPE_OFFSPRING = 11, 		# 徒弟或徒孙等产生的加分
}

# 系统类型
enum OS_TYPE {
	_OS_TYPE_UNKNOWN = 0,
	_OS_TYPE_ANDROID = 1,
	_OS_TYPE_IOS = 2,
}

#已分配的app_id
enum Apptype {
	_APP_ZHUAN = 0,
	_APP_WIFI = 1,
	_APP_GAME = 2,
}


struct ScoreAddObj {
	1:i32 uid,
	2:string device_id,
	3:i32 action_type,
	4:i32 currency,
	5:string pack_name,
	6:i32 trade_type,
	7:string ad_name,
	8:string order_id,
	9:i32 time_stamp,
	10:string client_ip,
	11:i32 app_id = 0,
	12:i32 os_type_id = 0,  # 0: unknown, 1: android, 2: ios
}

struct UserTicket{
	1:bool islogin, 
	2:string ticket
}

struct UserInfo {
	1:i32 uid,
	2:i64 mobile,
	3:string pword,
	4:string device_id,
	5:i32 from_app,
	6:string channel,
	7:i16 ulevel,
	# 总积分
	8:i32 total_score=0,	
	9:string ctime,
	10:i16 caution,
	# 今日得分
	11:i32 today_score=0,
	# 我邀请别人的id（现在是自己的uid） 
	12:i32 ic,
	13:string ic_content,
	14:string ic_url,
	15:i32 time_stamp,
	16:string os_type,
	17:string imsi,
	18:i32 status,
	19:string register_ip,
	# 余额
	20:i32 score=0,
	#邀请我的人的uid
	21:i32 invite_code=0,
	#邀请我的人的uid
	22:i32 point=0
}

#用户扩展信息
struct UserExInfo{
	1:i32 uid, 
	2:i32 sex,
	3:string birthday,
	4:i32 workspace,
	5:string ctime,
}

#工作场所
enum workSpace {
	# 学校
	ws_school = 1,
	# 写字楼/政府
	ws_goverment = 2,
	# 商场/医院/银行
	ws_bank = 3,
	# 地铁/机场/公交
	ws_subway = 4,
	# 工厂
	ws_factory = 5,
	# 在家
	ws_home = 6,
}


service UserService {
	bool ping(1:string str) throws (1:InvalidOperation ouch),
	
	bool test(1:string str),

	/**
	* register user
	*/
	i32 registerUser(1:UserAddObj userobj) throws (1:InvalidOperation ouch),
	
	/**
	* user login
	*/
	UserTicket userLogin(1:i64 pnum,2:string pw,3:string device_id,4:string os_type,5:string client_ip,6:i32 app_id,7:string imsi,8:string channel) throws (1:InvalidOperation ouch),
	
	/**
	* validate user
	*/
	UserInfo validateUserToken(1:string token,2:i32 app_id) throws (1:InvalidOperation ouch),
	
	/**
	* get Ticket
	*/
	UserTicket getTicket(1:i32 uid,2:string device_id,3:string pw) throws (1:InvalidOperation ouch),
	
	
	bool cacheUpdateUserInfo(1:i32 uid,2:string device_id),
	
	#用户注册
	i32 addUser(1:UserAddObj useraddobj),
	
	#用户在app注册 不在此注册将导致不能登陆成功
	bool addAppRegister(1:i32 uid,2:i32 app_id,3:string device_id,4:string imsi,5:string os_type,6:string channel,7:string client_ip),
	
	#判断用户是否已经在app注册 判断成功返回uid 失败 0
	bool existAppRegister(1:i32 uid,2:i32 app_id),
	
	#修改用户密码
	bool updateUserPassword(1:string password,2:i32 uid,3:i64 pnum),
	
	#修改用户状态(1)
	bool updateUserStatus(1:i32 uid,2:i32 status),
	
	#修改用户device_id信息
	bool updateUserDeviceId(1:i32 uid,2:string old_device_id,3:string new_device_id,4:i32 app_id),
	
	#删除用户
	bool delUser(1:i64 pnum),

	# 删除用户(上面属于物理删除，这个接口只是在数据上做标记)
	bool delUserEx(1:i64 pnum),
	
	#pnum 取得用户信息 
	UserInfo getUserInfo(1:i64 pnum,2:string ip,3:i32 is_ic,4:i32 app_id) throws (1:InvalidOperation ouch),

	#uid 取得用户信息 只会取得状态为1的有效用户
	UserInfo getUserInfoByUid(1:i32 uid,2:string ip,3:i16 is_ic,4:i32 app_id) throws (1:InvalidOperation ouch),
	
	#uid 取得用户信息 这个方法会取得所有用户 包括状态等于0 或 等于2的
	UserInfo getUserInfoByUidAllUser(1:i32 uid,2:string ip,3:i16 is_ic,4:i32 app_id) throws (1:InvalidOperation ouch),
	
	#pnum 取得用户信息 
	UserInfo getUserInfoAllUser(1:i64 pnum,2:string ip,3:i32 is_ic,4:i32 app_id) throws (1:InvalidOperation ouch),
	
	#取得uid by device id
	i32 getUidByDeviceId(1:string device_id,2:i32 app_id) throws (1:InvalidOperation ouch),
	
	#取得uid by pnum
	i32 getUidByPnum(1:i64 pnum),
	
	#用户是否关小黑屋
	bool getUserCaution(1:i32 uid,2:string ip),
	
	#用户是否关小黑屋 by ip
	bool getUserCautionByIp(1:string ip),
	
	#用户是否存在
	bool existUser(1:i32 uid),
	
	#用户验证有效性
	bool validateUser(1:i64 pnum,2:string password,3:string ip,4:string device_id,5:i32 uid,6:i32 app_id),
	
	#用户是否达到每日积分上限
	bool userScoreMaxCheck(1:i32 uid,2:i32 score),
	
	#加积分
	bool addScore(1:ScoreAddObj scoreadd),
	
	#取得用户余额
	i32 getUserBalance(1:i32 uid),
	
	#取得用户积分列表（含余额）
	map<string,i32> getUserScoreList(1:i32 uid) throws (1:InvalidOperation ouch),
	
	#取得用户今日积分列表
	map<string,i32> getUserTodayScoreList(1:i32 uid,2:bool is_yesteday),
	
	# 取得用户贡献值
	map<string,i32> getUserPointById(1:i32 uid),
	
	# 更新用户贡献值
	bool updateUserPoint(1:i32 uid,2:i32 point,3:i32 subpoint),
	
	# 取得用户邀请数量
	i32 getInviteMember(1:i32 uid),
	
	# 判断是否是测试用户 （这部分用户可删除、可ops加钱、但是不可以兑换）
	bool isTestUser(1:i64 pnum),
	
	#取得用户扩展信息
	UserExInfo getUserExInfo(1:i32 uid) throws (1:InvalidOperation ouch),
	
	#创建用户扩展信息
	bool createUserExInfo(1:UserExInfo userexinfo) throws (1:InvalidOperation ouch),

	# 获取用户当月积分变化情况的次数
	i32 getUserThisMonthScoreTime(1:i32 uid, 2:i32 action_type),

	# 修改用户手机号，只允许 web 版未绑定过手机号的用户使用(也就是手机号是 200 开头的)。失败返回具体原因，成功返回空字符串
	string updateUserMobile(1:i32 uid, 2:i64 pnum),

	# 获取用户七天内是否有过广告下载和邀请行为(临时的接口)
	bool checkUserAdOrInviteInSevenDays(1:i32 uid, 2:string sdate)

	# 获取用户可用于小额兑换的广告次数
	string getUserSmallExchangeAllAdTime(1:i32 uid)

	# 获取用户首次下载的广告的价钱
	i32 getUserFirstAdScore(1:i32 uid)

	# 添加一个小额兑换
	bool addSmallExchange(1:i32 uid, 2:string type_score)

	# 完成一个小额兑换
	bool finishSmallExchange(1:i32 uid, 2:string type_score, 3:bool succ)

	# 添加用户手机上的 app 安装或卸载记录(action_log 是一个json字符串，{'包名1': <0卸载, 1安装>, '包名2': <0卸载, 1安装>})
	bool addUserAppActionLog(1:i32 uid, 2:string device_id, 3:string action_log)

	# 更改用户的余额，以使用户收支平衡，从而可以参加兑换
	bool resumeUserScoreForExchange(1:i64 uid, 2:i32 score)

	# 管理员后台更改用户手机号
	string updateUserMobileForAdmin(1:i64 uid, 2:i64 old_mobile, 3:i64 new_mobile)

	# 消耗下载广告的次数(给一元夺宝使用)
	bool consumeAdDownloadTimes(1:i64 uid, 2:i32 times)
}



