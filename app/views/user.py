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
from app.models import UserRole, RoleMenu, User, Menu
from app.utils.ResponseWrap import successResponseWrap, failResponseWrap

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

    access_token = create_access_token(identity=user.userId, fresh=True)
    refresh_token = create_refresh_token(identity=user.userId)

    return successResponseWrap("登陆成功", data={"access_token": access_token, "refresh_token": refresh_token})


# 刷新JWT
@user.post("/user/refresh_token")
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity, fresh=False)
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
        "role_type": user_role.role_id,
        "permissions": menus
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
    db.session.add(User(username=username, password=password, registration_time=registration_time))
    db.session.commit()

    return successResponseWrap("添加成功")


# 查询所有用户信息
@user.get("/user/list")
@jwt_required()
def getUserList():
    # userId = get_jwt_identity()

    users = User.query.all()
    userList = []
    for u in users:
        userList.append({
            "userId": u.userId,
            "username": u.username,
            "email": u.email,
            "avatar": u.avatar,
            "gender": u.gender,
            "introduction": u.introduction,
            "registration_time": u.registration_time
        })

    return successResponseWrap(data=userList)
