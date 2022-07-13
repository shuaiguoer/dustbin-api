# !/usr/bin/env python
# -*-coding: utf-8 -*-
"""
# @File    : role.py
# @Time    : 2022/7/13 14:58
# @Author  : Shuai
# @Email   : ls12345666@qq.com
"""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from app.models import Role
from app.utils.ResponseWrap import successResponseWrap

role = Blueprint('role', __name__)


@role.get("/role/list")
@jwt_required()
def getRoleList():
    roles = Role.query.all()
    roleList = []
    for r in roles:
        roleList.append({
            "label": r.name,
            "value": r.id
        })
    return successResponseWrap(data=roleList)
