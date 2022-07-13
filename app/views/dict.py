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


@dictionary.get("/dict/gender")
def getGenderList():
    data = [
        {"label": "男", "value": 1},
        {"label": "女", "value": 0},
    ]
    return successResponseWrap(data=data)
