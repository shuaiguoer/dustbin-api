# !/usr/bin/env python3
# -*-coding: utf-8 -*-
"""
# @File    : user.py
# @Time    : 2022/7/8 23:29
# @Author  : Shuai
# @Email   : ls12345666@qq.com
"""
import time
import random

from flask import Blueprint, request, current_app
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, jwt_required

from app import db
from app.models import UserRole, RoleMenu, User, Menu, Role
from app.modules.VerifyAuth import role_required, permission_required
from app.utils.ResponseWrap import successResponseWrap, failResponseWrap
from app.utils.SendMail import send_email
from app.utils.ConnectionRedis import redisConnection

user = Blueprint('user', __name__)


# 用户登录
@user.post("/user/login")
def login():
    username = request.json.get("username")
    password = request.json.get("password")

    db_user = db.session.query(User.userId, User.password) \
        .filter(db.or_(User.username == username, User.email == username)).first()

    if db_user is None:
        return failResponseWrap(2004, "用户不存在")

    # 连接Redis
    redis2 = redisConnection(2)

    # 密码错误
    if password != db_user.password:
        LOGIN_ERR_MAX = current_app.config.get('LOGIN_ERR_MAX')
        LOGIN_LOCK_TIME = current_app.config.get('LOGIN_LOCK_TIME')

        #  向Redis中写入错误次数
        redis2.incr(db_user.userId)

        # 获取错误登录次数
        login_err_quantity = int(redis2.get(db_user.userId))

        # 错误登录次数 对比 错误登录最大限制次数
        if login_err_quantity <= LOGIN_ERR_MAX:
            # 设置过期时间
            redis2.expire(db_user.userId, LOGIN_LOCK_TIME)
        else:
            if login_err_quantity == LOGIN_ERR_MAX + 1:
                # 设置过期时间
                redis2.expire(db_user.userId, LOGIN_LOCK_TIME)

            # 获取距离登录限制解除的剩余时间
            expiration_time = redis2.ttl(db_user.userId)
            return failResponseWrap(2002, f"您登录失败的次数过多! 请等待 {expiration_time} 秒后重试!")

        return failResponseWrap(2002, f"账号或者密码错误! 剩余重试次数: {LOGIN_ERR_MAX - login_err_quantity}")

    # 密码正确
    # 如果存在错误密码次数记录, 则删除
    if redis2.exists(db_user.userId):
        redis2.delete(db_user.userId)

    access_token = create_access_token(identity=db_user.userId, fresh=True)
    refresh_token = create_refresh_token(identity=db_user.userId)

    return successResponseWrap("登陆成功", data={"access_token": access_token, "refresh_token": refresh_token})


# 刷新JWT
@user.post("/user/refresh_token")
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()

    # 获取用户角色
    db_role = Role.query.join(UserRole).filter_by(user_id=identity).first()

    access_token = create_access_token(identity=identity, fresh=False, additional_claims={"role": db_role.name})
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
        "gender": user.gender,
        "introduction": user.introduction,
        "registration_time": user.registration_time,
        "roleId": user_role.role_id,
        "permissions": menus
    }

    return successResponseWrap(data=userInfo)


# 获取指定用户信息
@user.get("/user/info/<int:userId>")
@permission_required("user-read")
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
    user = User.query.filter_by(username=username).first()
    if user:
        return failResponseWrap(2005, "用户已存在")

    # 判断邮箱是否重复绑定
    emails = db.session.query(User.email).all()
    emailList = [e[0] for e in emails]

    if email in emailList:
        return failResponseWrap(2006, "邮箱重复绑定")

    # 连接redis
    redis_1 = redisConnection(1)
    if not redis_1.exists(email):
        return failResponseWrap(2007, "验证码已过期")

    # 获取验证码
    redis_code = redis_1.get(email)

    if code != redis_code:
        return failResponseWrap(2008, "验证码错误")

    # 验证成功则删除缓存的验证码
    redis_1.delete(email)

    registration_time = int(round(time.time() * 1000))

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


# 获取所有用户信息
@user.get("/user/list")
@permission_required("user-list")
def getUserList():
    db_users_role = db.session.query(User, Role) \
        .join(UserRole, User.userId == UserRole.user_id) \
        .join(Role, UserRole.role_id == Role.id).all()

    userList = []

    for ur in db_users_role:
        userList.append({
            "userId": ur[0].userId,
            "username": ur[0].username,
            "email": ur[0].email,
            "avatar": ur[0].avatar,
            "gender": ur[0].gender,
            "introduction": ur[0].introduction,
            "registration_time": ur[0].registration_time,
            "roleNickName": ur[1].nickname
        })

    return successResponseWrap(data=userList)


# 添加用户
@user.post("/user/add")
@permission_required("user-add")
def addUser():
    username = request.json.get("username")
    email = request.json.get("email")
    gender = request.json.get("gender")
    introduction = request.json.get("introduction")
    roleId = request.json.get("roleId")

    # 判断用户名是否存在
    user = User.query.filter_by(username=username).first()
    if user:
        return failResponseWrap(2005, "用户已存在")

    registration_time = int(round(time.time() * 1000))

    # 写入数据库
    userInfo = User(username=username, email=email, gender=gender, introduction=introduction,
                    registration_time=registration_time)
    db.session.add(userInfo)

    # 预提交(写入内存)
    db.session.flush()

    # 默认设置为普通用户
    db.session.add(UserRole(user_id=userInfo.userId, role_id=roleId))

    # 提交(写入硬盘)
    db.session.commit()

    return successResponseWrap("添加成功")


# 更新用户信息
@user.put("/user/update")
@permission_required("user-update")
def updateUser():
    userId = request.json.get("userId")
    username = request.json.get("username")
    email = request.json.get("email")
    gender = request.json.get("gender")
    introduction = request.json.get("introduction")
    roleId = request.json.get("roleId")

    # 更新用户信息
    User.query.filter_by(userId=userId) \
        .update({"username": username, "email": email, "gender": gender, "introduction": introduction})

    # 更新用户角色
    result = UserRole.query.filter_by(user_id=userId).update({"role_id": roleId})

    if not result:
        return failResponseWrap(5001, "没有数据被更新")

    db.session.commit()

    return successResponseWrap("更新成功")


# 删除用户
@user.delete("/user/delete/<int:userId>")
@permission_required("user-delete")
def deleteUser(userId):
    # 删除用户角色关系
    UserRole.query.filter_by(user_id=userId).delete()

    # 删除用户信息
    result = User.query.filter_by(userId=userId).delete()

    if not result:
        return failResponseWrap(5001, "未找到您要删除的用户")

    db.session.commit()

    return successResponseWrap("删除成功")


# 重置用户密码
@user.put("/user/reset-password/<int:userId>")
@permission_required("user-update")
def resetUserPassword(userId):
    result = User.query.filter_by(userId=userId).update({"password": "123456"})

    if not result:
        return failResponseWrap(5001, "没有数据被更新")

    db.session.commit()

    return successResponseWrap("密码重置成功")


# 查询符合条件的用户
@user.get("/user/query")
@permission_required("user-list")
def queryUser():
    username = request.args.get("username") or ''
    email = request.args.get("email") or ''
    roleId = request.args.get("roleId") or ''

    db_users_role = db.session.query(User, Role) \
        .join(UserRole, User.userId == UserRole.user_id) \
        .join(Role, UserRole.role_id == Role.id) \
        .filter(User.username.like(f'%{username}%'),
                User.email.like(f'%{email}%'),
                UserRole.role_id.like(f'%{roleId}%')).all()

    userList = []

    for ur in db_users_role:
        userList.append({
            "userId": ur[0].userId,
            "username": ur[0].username,
            "email": ur[0].email,
            "avatar": ur[0].avatar,
            "gender": ur[0].gender,
            "introduction": ur[0].introduction,
            "registration_time": ur[0].registration_time,
            "roleNickName": ur[1].nickname
        })

    return successResponseWrap(data=userList)
