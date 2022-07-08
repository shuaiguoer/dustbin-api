# !/usr/bin/env python3
# -*-coding: utf-8 -*-
"""
# @File    : user.py
# @Time    : 2022/7/8 23:29
# @Author  : Shuai
# @Email   : ls12345666@qq.com
"""
from flask import Blueprint, jsonify
from app import db
from app.models import User

user = Blueprint('user', __name__)


@user.get("/user/info")
def getUserInfo():
    # 查询
    db_users = db.session.query(User).all()
    # db_users = User.query.all()
    users = []
    for user in db_users:
        users.append(user.to_json())

    return jsonify(users)
