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
from app.models import Role, Menu, RoleMenu
from app.utils.ResponseWrap import successResponseWrap
from app.modules.VerifyAuth import role_required
from app.utils.GenerateMenus import generateMenuTree, filterRoleTree

role = Blueprint('role', __name__)


# 获取角色列表
@role.get("/role/list")
@jwt_required()
def getRoleList():
    page = request.args.get("page", type=int)
    pageSize = request.args.get("pageSize", type=int)

    # 查询所有角色
    roles = Role.query.slice(pageSize * (page - 1), pageSize * page).all()

    roleList = [r.to_json() for r in roles]

    # 查询角色总数量
    itemCount = db.session.query(db.func.count(Role.id)).scalar()

    # 获取总页数
    pageCount = int((itemCount + pageSize - 1) / pageSize)

    roleData = {
        "list": roleList,
        "page": page,
        "pageSize": pageSize,
        "pageCount": pageCount,
        "itemCount": itemCount,
    }

    return successResponseWrap(data=roleData)
