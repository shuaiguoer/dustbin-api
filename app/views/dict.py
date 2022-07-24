# !/usr/bin/env python
# -*-coding: utf-8 -*-
"""
# @File    : dict.py
# @Time    : 2022/7/13 15:32
# @Author  : Shuai
# @Email   : ls12345666@qq.com
"""
from flask import Blueprint, request

from app import db
from app.models import Role

from flask_jwt_extended import jwt_required
from app.utils.ResponseWrap import successResponseWrap

dictionary = Blueprint('dictionary', __name__)


# 性别
@dictionary.get("/dict/gender")
@jwt_required()
def getGender():
    data = [
        {"label": "女", "value": 0},
        {"label": "男", "value": 1},
    ]
    return successResponseWrap(data=data)


# 角色
@dictionary.get("/dict/role")
@jwt_required()
def getRole():
    db_roles = Role.query.all()

    roleDict = [{"label": r.nickname, "value": r.id} for r in db_roles]

    return successResponseWrap(data=roleDict)
