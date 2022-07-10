# !/usr/bin/env python3
# -*-coding: utf-8 -*-
"""
# @File    : user.py
# @Time    : 2022/7/8 23:29
# @Author  : Shuai
# @Email   : ls12345666@qq.com
"""
from flask import Blueprint, request
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, jwt_required

from app import db
from app.models import UserRole, RoleMenu, User, Menu
from app.utils.ResponseWrap import successResponseWrap, failResponseWrap

user = Blueprint('user', __name__)


# 用户登录
@user.post("/user/login")
def login():
    username, password = request.get_json().values()

    user = db.session.query(User.userId, User.password) \
        .filter(db.or_(User.username == username, User.email == username)).first()

    if user is None:
        return failResponseWrap(2004, "用户不存在")

    if password != user.password:
        return failResponseWrap(2002, "账号或者密码错误!")

    access_token = create_access_token(identity=user.userId)
    refresh_token = create_refresh_token(identity=user.userId)

    return successResponseWrap("登陆成功", data={"access_token": access_token, "refresh_token": refresh_token})


# 刷新JWT
@user.post("/user/refresh_token")
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    print(identity)
    access_token = create_access_token(identity=identity)
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
