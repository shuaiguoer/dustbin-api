# !/usr/bin/env python3
# -*-coding: utf-8 -*-
"""
# @File    : user.py
# @Time    : 2022/7/8 23:29
# @Author  : Shuai
# @Email   : ls12345666@qq.com
"""
import os
import random
import time

from flask import Blueprint, request, current_app
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, jwt_required, get_jwt, \
    get_jti
from werkzeug.utils import secure_filename

from app import db
from app.conf.StatusCode import TOKEN_IN_BLACKLIST
from app.models import UserRole, RoleMenu, User, Menu, Role
from app.modules.VerifyAuth import permission_required
from app.modules.VerifyEmail import verifyEmail
from app.utils.ConnectionRedis import redisConnection
from app.utils.Encrypt import md5
from app.utils.ResponseWrap import successResponseWrap, failResponseWrap
from app.utils.SendMail import send_email
from app.utils.WriteLog import writeLoginLog, writeOperationLog, getUserLoginInfo

user = Blueprint('user', __name__)


# 用户登录
@user.post("/user/login")
def login():
    username = request.json.get("username")
    password = request.json.get("password")
    LOGIN_ERR_MAX = current_app.config.get('LOGIN_ERR_MAX')
    LOGIN_LOCK_TIME = current_app.config.get('LOGIN_LOCK_TIME')

    db_user = db.session.query(User.userId, User.password, User.username) \
        .filter(db.or_(User.username == username, User.email == username)) \
        .first()

    if db_user is None:
        # 记录日志
        writeLoginLog(username=username, status=1, msg="用户不存在", request=request)

        return failResponseWrap(2004, "用户不存在")

    # 连接Redis
    rdb_pwd_err_cnt = redisConnection(2)

    # 如果用户ID存在, 并且错误登录次数 大于 错误登录次数最大限制
    if rdb_pwd_err_cnt.exists(db_user.userId) and int(rdb_pwd_err_cnt.get(db_user.userId)) >= LOGIN_ERR_MAX:
        # 记录日志
        writeLoginLog(username=db_user.username, status=1,
                      msg=f"登陆次数过多, 已被锁定; 距离解锁: {rdb_pwd_err_cnt.ttl(db_user.id)} 秒", request=request)

        return failResponseWrap(2003, f"您登录失败的次数过多! 请等待 {rdb_pwd_err_cnt.ttl(db_user.userId)} 秒后重试!")

    # 密码加密
    password = md5(password)

    # 密码错误
    if password != db_user.password:
        #  向Redis中写入错误次数
        rdb_pwd_err_cnt.incr(db_user.userId)

        # 获取错误登录次数
        login_err_quantity = int(rdb_pwd_err_cnt.get(db_user.userId))

        # 错误登录次数 对比 错误登录最大限制次数
        if login_err_quantity < LOGIN_ERR_MAX:
            # 设置过期时间
            rdb_pwd_err_cnt.expire(db_user.userId, LOGIN_LOCK_TIME)
        else:
            if login_err_quantity == LOGIN_ERR_MAX:
                # 设置过期时间
                rdb_pwd_err_cnt.expire(db_user.userId, LOGIN_LOCK_TIME)
                return failResponseWrap(2003,
                                        f"您登录失败的次数过多! 请等待 {rdb_pwd_err_cnt.ttl(db_user.userId)} 秒后重试!")

        # 记录日志
        writeLoginLog(username=db_user.username, status=1, msg=f"账号或者密码输入错误 {login_err_quantity} 次",
                      request=request)

        return failResponseWrap(2002, f"账号或者密码错误! 剩余重试次数: {LOGIN_ERR_MAX - login_err_quantity}")

    # 密码正确
    # 如果存在错误密码次数记录, 则删除
    if rdb_pwd_err_cnt.exists(db_user.userId):
        rdb_pwd_err_cnt.delete(db_user.userId)

    additional_claims = {"username": db_user.username}
    access_token = create_access_token(identity=db_user.userId, fresh=True, additional_claims=additional_claims)
    refresh_token = create_refresh_token(identity=db_user.userId, additional_claims=additional_claims)

    # 记录日志
    login_log = writeLoginLog(username=db_user.username, status=0, msg="登陆成功", request=request)

    # 传入refresh_jti字段
    refresh_jti = get_jti(refresh_token)
    login_log["refresh_jti"] = refresh_jti

    # 记录在线用户
    jti = get_jti(access_token)
    ex = current_app.config.get("JWT_ACCESS_TOKEN_EXPIRES").seconds
    rdb_online_users = redisConnection(0)
    rdb_online_users.hmset(jti, login_log)
    rdb_online_users.expire(jti, ex)

    return successResponseWrap("登陆成功", data={"access_token": access_token, "refresh_token": refresh_token})


# 刷新JWT
@user.post("/user/refresh_token")
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    claims = get_jwt()
    username = claims["username"]
    refresh_jti = claims["jti"]

    # 效验refresh_token是否在黑名单中
    rdb_blacklist = redisConnection(1)
    if rdb_blacklist.exists(refresh_jti):
        return failResponseWrap(*TOKEN_IN_BLACKLIST)

    additional_claims = {"username": username}
    access_token = create_access_token(identity=identity, fresh=False, additional_claims=additional_claims)

    # 记录在线用户
    login_info = getUserLoginInfo(username=username, request=request)
    # 传入refresh_jti字段
    login_info["refresh_jti"] = refresh_jti
    jti = get_jti(access_token)

    ex = current_app.config.get("JWT_ACCESS_TOKEN_EXPIRES").seconds
    rdb_online_users = redisConnection(0)
    rdb_online_users.hmset(jti, login_info)
    rdb_online_users.expire(jti, ex)

    return successResponseWrap("刷新成功", data={"access_token": access_token})


# 获取用户信息
@user.get("/user/info")
@jwt_required()
def getUserInfo():
    userId = get_jwt_identity()

    # 获取用户对象
    user = User.query.filter_by(userId=userId).first()

    # 获取用户角色关系对象
    user_role = UserRole.query.filter_by(user_id=userId).first()

    # 获取菜单
    db_menus = db.session.query(Menu).select_from(UserRole) \
        .join(RoleMenu, UserRole.role_id == RoleMenu.role_id) \
        .join(Menu, RoleMenu.menu_id == Menu.id) \
        .join(User, UserRole.user_id == User.userId) \
        .filter(User.userId == userId, RoleMenu.deleted == 0).all()

    # 查询角色名称
    db_role = Role.query.join(UserRole).filter(UserRole.user_id == user.userId).first()

    menus = []
    for menu in db_menus:
        menus.append({
            "label": menu.title,
            "value": menu.name,
            "routeName": menu.name,
            "routeUrl": menu.path,
            "menuType": menu.type
        })

    userInfo = {
        "userId": user.userId,
        "username": user.username,
        "email": user.email,
        "avatar": user.avatar,
        "gender": str(user.gender),
        "introduction": user.introduction,
        "registration_time": user.registration_time,
        "roleId": user_role.role_id,
        "roleName": db_role.nickname,
        "permissions": menus
    }

    return successResponseWrap(data=userInfo)


# 获取指定用户信息
@user.get("/user/info/<int:userId>")
@permission_required("user:read")
def getSomeUserInfo(userId):
    user = User.query.filter(User.userId == userId).first()

    userInfo = {
        "userId": userId,
        "username": user.username,
        "email": user.email,
        "gender": user.gender,
        "introduction": user.introduction,
        "roleId": user.user_roles[0].role_id
    }

    return successResponseWrap(data=userInfo)


# 用户注册
@user.post("/user/register")
def register():
    username = request.json.get("username")
    password = request.json.get("password")
    retPassword = request.json.get("retPassword")
    email = request.json.get("email")
    code = request.json.get("code")

    if not username:
        return failResponseWrap(1002, "用户名不能为空")

    if not email:
        return failResponseWrap(1002, "邮箱地址不能为空")

    if not code:
        return failResponseWrap(1002, "验证码不能为空")

    if password != retPassword:
        return failResponseWrap(2009, "两次输入的密码不一致!")

    # 判断用户名是否存在
    db_user = User.query.filter_by(username=username).first()
    if db_user:
        return failResponseWrap(2005, "用户已存在")

    # 判断邮箱是否重复绑定
    db_user = User.query.filter_by(email=email).first()
    if db_user:
        return failResponseWrap(2006, "邮箱重复绑定")

    # 效验验证码
    result = verifyEmail(email, code)

    # 如果存在code字段, 说明效验失败
    if type(result) == dict:
        return result

    registration_time = int(round(time.time() * 1000))

    # 密码加密
    password = md5(password)

    # 写入数据库
    userInfo = User(username=username, password=password, email=email, registration_time=registration_time)
    db.session.add(userInfo)

    # 预提交(写入内存)
    db.session.flush()

    # 默认设置为普通用户
    db.session.add(UserRole(user_id=userInfo.userId, role_id=2))

    # 提交(写入硬盘)
    db.session.commit()

    return successResponseWrap("添加成功")


# 生成验证码
@user.post("/user/generate_code")
def generate_code():
    email = request.json.get("email")

    if not email:
        return failResponseWrap(1002, "邮箱地址不能为空")

    # 随机生成验证码
    code = str(random.randint(1000, 9999))

    # 连接redis数据库
    redis_1 = redisConnection(1)

    # 将验证码写入redis数据库, 并设置过期时间为300秒
    redis_1.setex(email, 300, code)

    # 发送邮件
    send_email("Dustbin-验证码", code, [email])

    return successResponseWrap("验证码生成成功")


# 找回密码
@user.post("/user/recover_password")
def recover_password():
    email = request.json.get("email")
    password = request.json.get("password")
    retPassword = request.json.get("retPassword")
    code = request.json.get("code")

    if not email:
        return failResponseWrap(1002, "邮箱地址不能为空")

    if not code:
        return failResponseWrap(1002, "验证码不能为空")

    if password != retPassword:
        return failResponseWrap(2009, "两次输入的密码不一致!")

    # 检查验证码是否正确
    redis_1 = redisConnection(1)
    if not redis_1.exists(email):
        return failResponseWrap(2007, "验证码已过期")
    redis_code = redis_1.get(email)
    if code != redis_code:
        return failResponseWrap(2008, "验证码错误")
    redis_1.delete(email)

    result = User.query.filter_by(email=email).update({"password": password})

    if not result:
        return failResponseWrap(5001, "没有数据被更新")

    db.session.commit()

    return successResponseWrap("密码修改成功")


# 获取用户列表
@user.get("/user/list")
@permission_required("user:list")
def getUserList():
    username = request.args.get("username")
    email = request.args.get("email")
    roleId = request.args.get("roleId")
    page = request.args.get("page", type=int)
    pageSize = request.args.get("pageSize", type=int)

    filter_params = []
    if username:
        filter_params.append(User.username.like(f'%{username}%'))
    if email:
        filter_params.append(User.email.like(f'%{email}%'))
    if roleId:
        filter_params.append(UserRole.role_id == roleId)

    db_user = db.session.query(User) \
        .join(UserRole, User.userId == UserRole.user_id) \
        .join(Role, UserRole.role_id == Role.id) \
        .filter(*filter_params) \
        .limit(pageSize).offset(pageSize * (page - 1)) \
        .all()

    userList = []

    for u in db_user:
        db_role = Role.query.join(UserRole, Role.id == UserRole.role_id).filter(UserRole.user_id == u.userId).first()

        userList.append({
            "userId": u.userId,
            "username": u.username,
            "email": u.email,
            "avatar": u.avatar,
            "gender": u.gender,
            "introduction": u.introduction,
            "registration_time": u.registration_time,
            "roleNickName": db_role.nickname
        })

    # 查询当前部门的用户总数量
    itemCount = db.session.query(db.func.count(User.userId)) \
        .join(UserRole, User.userId == UserRole.user_id) \
        .join(Role, UserRole.role_id == Role.id) \
        .filter(*filter_params).scalar()

    # 获取总页数
    pageCount = int((itemCount + pageSize - 1) / pageSize)

    userData = {
        "list": userList,
        "page": page,
        "pageSize": pageSize,
        "pageCount": pageCount,
        "itemCount": itemCount,
    }

    return successResponseWrap(data=userData)


# 添加用户
@user.post("/user/add")
@permission_required("user:add")
def addUser():
    username = request.json.get("username")
    email = request.json.get("email")
    gender = request.json.get("gender")
    introduction = request.json.get("introduction")
    roleId = request.json.get("roleId")

    claims = get_jwt()
    myName = claims["username"]

    # 判断用户名是否存在
    db_user = User.query.filter_by(username=username).first()
    if db_user:
        return failResponseWrap(2005, "用户已存在")

    # 判断邮箱是否重复绑定
    db_user = User.query.filter_by(email=email).first()
    if db_user:
        return failResponseWrap(2006, "邮箱重复绑定")

    password = current_app.config.get("DEFAULT_USER_PASSWORD")
    registration_time = int(round(time.time() * 1000))

    # 写入数据库
    userInfo = User(username=username, password=password, email=email, gender=gender, introduction=introduction,
                    registration_time=registration_time)
    db.session.add(userInfo)

    # 预提交(写入内存)
    db.session.flush()

    # 默认设置为普通用户
    db.session.add(UserRole(user_id=userInfo.userId, role_id=roleId))

    # 提交(写入硬盘)
    db.session.commit()

    successResponse = successResponseWrap("添加成功")

    # 记录日志
    writeOperationLog(username=myName, systemModule="添加用户", operationType=1, status=0, returnParam=successResponse,
                      request=request)

    return successResponse


# 更新用户信息
@user.put("/user/update")
@permission_required("user:update")
def updateUser():
    userId = request.json.get("userId")
    username = request.json.get("username")
    email = request.json.get("email")
    gender = request.json.get("gender")
    introduction = request.json.get("introduction")
    roleId = request.json.get("roleId")

    claims = get_jwt()
    myName = claims["username"]

    # 更新用户信息
    User.query.filter_by(userId=userId) \
        .update({"username": username, "email": email, "gender": gender, "introduction": introduction})

    # 更新用户角色
    result = UserRole.query.filter_by(user_id=userId).update({"role_id": roleId})

    if not result:
        return failResponseWrap(5001, "没有数据被更新")

    db.session.commit()

    successResponse = successResponseWrap("更新成功")

    # 记录日志
    writeOperationLog(username=myName, systemModule="更新用户", operationType=2, status=0, returnParam=successResponse,
                      request=request)

    return successResponse


# 删除用户
@user.delete("/user/delete/<int:userId>")
@permission_required("user:delete")
def deleteUser(userId):
    claims = get_jwt()
    myName = claims["username"]

    # 删除用户角色关系
    UserRole.query.filter_by(user_id=userId).delete()

    # 删除用户信息
    result = User.query.filter_by(userId=userId).delete()

    if not result:
        return failResponseWrap(5001, "未找到您要删除的用户")

    db.session.commit()

    successResponse = successResponseWrap("删除成功")

    # 记录日志
    writeOperationLog(username=myName, systemModule="删除用户", operationType=3, status=0, returnParam=successResponse,
                      request=request)

    return successResponse


# 重置用户密码
@user.put("/user/reset-password/<int:userId>")
@permission_required("user:update")
def resetUserPassword(userId):
    claims = get_jwt()
    myName = claims["username"]

    password = current_app.config.get("DEFAULT_USER_PASSWORD")
    result = User.query.filter_by(userId=userId).update({"password": password})

    if not result:
        return failResponseWrap(5001, "没有数据被更新")

    db.session.commit()

    successResponse = successResponseWrap("密码重置成功")

    # 记录日志
    writeOperationLog(username=myName, systemModule="重置用户密码", operationType=2, status=0,
                      returnParam=successResponse, request=request)

    return successResponse


# 更改个人密码
@user.put("/user/own-password/update")
@jwt_required()
def updateOwnPassword():
    userId = get_jwt_identity()
    oldPassword = request.json.get("oldPassword")
    password = request.json.get("password")
    rePassword = request.json.get("rePassword")

    if password != rePassword:
        return failResponseWrap(2009, "两次输入的密码不一致!")

    db_user = User.query.filter_by(userId=userId).first()

    # 验证数据库密码是否与用户输入的原密码相同
    if md5(oldPassword) != db_user.password:
        return failResponseWrap(2002, "原密码不正确")

    # 将新密码写入数据库
    result = User.query.filter_by(userId=userId).update({"password": md5(password)})

    if not result:
        return failResponseWrap(5001, "未知原因, 密码未被更新")

    db.session.commit()

    return successResponseWrap("密码修改成功")


# 更新个人信息
@user.put("/user/own-info/update")
@jwt_required()
def updateOwnInfo():
    userId = get_jwt_identity()
    avatar = request.json.get("avatar")
    username = request.json.get("username")
    email = request.json.get("email")
    gender = request.json.get("gender")
    introduction = request.json.get("introduction")
    UPLOAD_FOLDER = current_app.config.get("UPLOAD_FOLDER")

    # 查询用户头像
    db_user = User.query.filter_by(userId=userId).first()
    db_user_avatar = db_user.avatar
    avatar_path = request.host_url + UPLOAD_FOLDER

    # 判断文件目录是否存在用户头像
    if db_user_avatar and db_user_avatar.find(avatar_path) != -1:
        # 删除原头像
        old_avatar = db_user_avatar.split(request.host_url)[1]
        if os.path.exists(old_avatar):
            os.remove(old_avatar)

    User.query.filter_by(userId=userId).update(
        {"username": username, "gender": gender, "email": email, "introduction": introduction, "avatar": avatar}
    )

    db.session.commit()

    return successResponseWrap("信息更新成功")


# 效验验证码
@user.post("/user/verification-code")
def verificationCode():
    email = request.json.get("email")
    code = request.json.get("code")

    # 效验验证码
    result = verifyEmail(email, code)

    # 如果存在code字段, 说明效验失败
    if type(result) == dict:
        return result

    return successResponseWrap("验证码效验成功")


# 换绑邮箱
@user.put("/user/own-email/update")
@jwt_required()
def updateOwnEmail():
    userId = get_jwt_identity()
    email = request.json.get("email")
    code = request.json.get("code")

    # 判断邮箱是否重复绑定
    db_user = User.query.filter_by(email=email).first()
    if db_user:
        return failResponseWrap(2006, "邮箱重复绑定")

    # 效验验证码
    verifyResult = verifyEmail(email, code)

    if type(verifyResult) == dict:
        return verifyResult

    result = User.query.filter_by(userId=userId).update({"email": email})

    if not result:
        return failResponseWrap(5001, "没有数据被更新")

    db.session.commit()

    return successResponseWrap("邮箱已绑定成功")


# 更新头像
@user.post("/user/avatar/update")
@jwt_required()
def updateAvatar():
    userId = get_jwt_identity()

    UPLOAD_FOLDER = current_app.config.get("UPLOAD_FOLDER")
    ALLOWED_EXTENSIONS = current_app.config.get("ALLOWED_EXTENSIONS")

    if 'avatar' not in request.files:
        return failResponseWrap(1002, "未接收到文件")

    avatar = request.files.get("avatar")
    filename = avatar.filename

    if filename == '':
        return failResponseWrap(1002, "接收到空文件")

    if filename.rsplit('.', 1)[1].lower() not in ALLOWED_EXTENSIONS:
        return failResponseWrap(1003, "不支持的文件类型")

    if avatar and '.' in filename:
        ts = int(round(time.time() * 1000))
        filename = secure_filename(filename)
        avatar_filename = str(userId) + str(ts) + filename

        db_user = User.query.filter_by(userId=userId).first()
        db_user_avatar = db_user.avatar
        avatar_path = request.host_url + UPLOAD_FOLDER

        # 判断文件目录是否存在用户头像
        if db_user_avatar and db_user_avatar.find(avatar_path) != -1:
            # 删除原头像
            old_avatar = db_user_avatar.split(request.host_url)[1]
            if os.path.exists(old_avatar):
                os.remove(old_avatar)

        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)

        avatar.save(os.path.join(UPLOAD_FOLDER, avatar_filename))

        avatar_url = request.host_url + UPLOAD_FOLDER + avatar_filename

        User.query.filter_by(userId=userId).update({"avatar": avatar_url})

        db.session.commit()

        return successResponseWrap("上传成功")

    return failResponseWrap(-1, "上传失败")


# 用户登出
@user.post("/user/logout")
@jwt_required()
def logout():
    refresh_token = request.json.get("refresh_token")

    # 从在线用户中删除
    claims = get_jwt()
    jti = claims["jti"]

    rdb_online_users = redisConnection(0)
    rdb_online_users.delete(jti)

    # 将refresh_token加入黑名单
    refresh_jti = get_jti(refresh_token)

    username = claims["username"]

    exp = claims["exp"]
    now = int(round(time.time()))
    ex = exp - now

    rdb_blacklist = redisConnection(1)
    rdb_blacklist.hmset(refresh_jti, {"username": username})
    rdb_blacklist.expire(refresh_jti, ex)

    return successResponseWrap("成功退出登录")


# 强制用户登出
@user.post("/user/forced-logout")
@permission_required("user:forced-logout")
def forcedLogout():
    refresh_jti = request.json.get("jti")
    username = request.json.get("username")

    claims = get_jwt()
    jti = claims["jti"]
    myName = claims["username"]

    rdb_online_users = redisConnection(0)
    rdb_online_users.delete(jti)

    ex = current_app.config.get("JWT_REFRESH_TOKEN_EXPIRES").days * 24 * 60 * 60
    access_ex = int(current_app.config.get("JWT_ACCESS_TOKEN_EXPIRES").seconds / 60)
    rdb_blacklist = redisConnection(1)
    rdb_blacklist.hmset(refresh_jti, {"username": username})
    rdb_blacklist.expire(refresh_jti, ex)

    successResponse = successResponseWrap(f"已发起强退, 将在{access_ex}分钟之内生效!")

    # 记录日志
    writeOperationLog(username=myName, systemModule="强退用户", operationType=5, status=0, returnParam=successResponse,
                      request=request)

    return successResponse
