# !/usr/bin/env python
# -*-coding: utf-8 -*-
"""
# @File    : dict.py
# @Time    : 2022/7/13 15:32
# @Author  : Shuai
# @Email   : ls12345666@qq.com
"""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from app.models import Role
from app.utils.ResponseWrap import successResponseWrap

dictionary = Blueprint('dictionary', __name__)


# 性别
@dictionary.get("/dict/gender")
def Gender():
    data = [
        {"label": "女", "value": 0},
        {"label": "男", "value": 1},
    ]
    return successResponseWrap(data=data)


# 角色
@dictionary.get("/dict/role")
def Role():
    data = [
        {"label": "管理员", "value": 1},
        {"label": "普通用户", "value": 2}
    ]
    return successResponseWrap(data=data)
