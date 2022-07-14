# !/usr/bin/env python3
# -*-coding: utf-8 -*-
"""
# @File    : user.py
# @Time    : 2022/7/8 23:29
# @Author  : Shuai
# @Email   : ls12345666@qq.com
"""
import time

from flask import Blueprint, request
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, jwt_required

from app import db
from app.models import UserRole, RoleMenu, User, Menu, Role
from app.utils.ResponseWrap import successResponseWrap, failResponseWrap
from app.modules.VerifyAuth import role_required

user = Blueprint('user', __name__)


# 用户登录
@user.post("/user/login")
def login():
    username = request.json.get("username")
    password = request.json.get("password")

    user = db.session.query(User.userId, User.password) \
        .filter(db.or_(User.username == username, User.email == username)).first()

    if user is None:
        return failResponseWrap(2004, "用户不存在")

    if password != user.password:
        return failResponseWrap(2002, "账号或者密码错误!")

    # 获取用户角色
    user_role = db.session.query(User, Role) \
        .join(UserRole, User.userId == UserRole.user_id) \
        .join(Role, UserRole.role_id == Role.id).filter(User.userId == user.userId).first()

    access_token = create_access_token(identity=user.userId, fresh=True, additional_claims={"role": user_role[1].name})
    refresh_token = create_refresh_token(identity=user.userId)

    return successResponseWrap("登陆成功", data={"access_token": access_token, "refresh_token": refresh_token})


# 刷新JWT
@user.post("/user/refresh_token")
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()

    # 获取用户角色
    user_role = db.session.query(User, Role) \
        .join(UserRole, User.userId == UserRole.user_id) \
        .join(Role, UserRole.role_id == Role.id).filter(User.userId == identity).first()

    access_token = create_access_token(identity=identity, fresh=False, additional_claims={"role": user_role[1].name})
    return successResponseWrap("刷新成功", data={"access_token": access_token})


# 用户信息
@user.get("/user/info")
@jwt_required()
def getUserInfo():
    userId = get_jwt_identity()

    # 获取用户对象
    user = db.session.query(User).filter_by(userId=userId).first()

    # 获取用户角色关系对象
    user_role = UserRole.query.filter_by(user_id=userId).first()

    # 获取菜单
    db_menus = db.session.query(Menu).select_from(UserRole) \
        .join(RoleMenu, UserRole.role_id == RoleMenu.role_id) \
        .join(Menu, RoleMenu.menu_id == Menu.id) \
        .join(User, UserRole.user_id == User.userId) \
        .filter(User.userId == userId).all()

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


# 查询指定用户信息
@user.get("/user/info/<int:userId>")
@role_required("admin")
def getSomeUserInfo(userId):
    user_role = db.session.query(User, UserRole).join(UserRole, User.userId == UserRole.user_id).filter(
        User.userId == userId).first()
    userInfo = {
        "userId": userId,
        "username": user_role[0].username,
        "roleId": user_role[1].role_id,
        "email": user_role[0].email,
        "gender": user_role[0].gender,
        "introduction": user_role[0].introduction
    }

    return successResponseWrap(data=userInfo)


# 用户注册
@user.post("/user/register")
def register():
    username = request.json.get("username")
    password = request.json.get("password")
    retPassword = request.json.get("retPassword")

    # 判断用户两次密码是否一致
    if password != retPassword:
        return failResponseWrap(2008, "两次输入的密码不一致!")

    # 判断用户名是否存在
    user = User.query.filter_by(username=username).first()
    if user:
        return failResponseWrap(2005, "用户已存在")

    registration_time = int(round(time.time() * 1000))

    # 写入数据库
    userInfo = User(username=username, password=password, registration_time=registration_time)
    db.session.add(userInfo)

    # 预提交(写入内存)
    db.session.flush()

    # 默认设置为普通用户
    db.session.add(UserRole(user_id=userInfo.userId, role_id=2))

    # 提交(写入硬盘)
    db.session.commit()

    return successResponseWrap("添加成功")


# 查询所有用户信息
@user.get("/user/list")
@role_required("admin")
def getUserList():
    user_role = db.session.query(User, Role) \
        .join(UserRole, User.userId == UserRole.user_id) \
        .join(Role, UserRole.role_id == Role.id).all()

    userList = []

    for u in user_role:
        userList.append({
            "userId": u[0].userId,
            "username": u[0].username,
            "email": u[0].email,
            "avatar": u[0].avatar,
            "gender": u[0].gender,
            "role": u[1].id,
            "introduction": u[0].introduction,
            "registration_time": u[0].registration_time
        })

    return successResponseWrap(data=userList)


# 添加用户
@user.post("/user/add")
@role_required("admin")
def addUser():
    username = request.json.get("username")
    password = request.json.get("password")
    retPassword = request.json.get("retPassword")
    email = request.json.get("email")
    gender = request.json.get("gender")
    introduction = request.json.get("introduction")
    roleId = request.json.get("roleId")

    # 判断用户两次密码是否一致
    if password != retPassword:
        return failResponseWrap(2008, "两次输入的密码不一致!")

    # 判断用户名是否存在
    user = User.query.filter_by(username=username).first()
    if user:
        return failResponseWrap(2005, "用户已存在")

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

    return successResponseWrap("添加成功")


# 更新用户信息
@user.post("/user/update")
@role_required("admin")
def updateUser():
    userId = request.json.get("userId")
    username = request.json.get("username")
    password = request.json.get("password")
    retPassword = request.json.get("retPassword")
    email = request.json.get("email")
    gender = request.json.get("gender")
    introduction = request.json.get("introduction")
    roleId = request.json.get("roleId")

    if password != retPassword:
        return failResponseWrap(2008, "两次输入的密码不一致!")

    # 更新用户信息
    User.query.filter_by(userId=userId).update(
        {"username": username, "password": password, "email": email, "gender": gender, "introduction": introduction}
    )

    # 更新用户角色
    UserRole.query.filter_by(user_id=userId).update({"role_id": roleId})

    db.session.commit()

    return successResponseWrap("更新成功")
