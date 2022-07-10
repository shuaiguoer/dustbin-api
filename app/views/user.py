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
from app.models import User, UserRole, Role, RoleMenu, Menu
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
