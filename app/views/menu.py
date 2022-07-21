# !/usr/bin/env python3
# -*-coding: utf-8 -*-
"""
# @File    : menu.py
# @Time    : 2022/7/10 17:09
# @Author  : Shuai
# @Email   : ls12345666@qq.com
"""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from app.models import UserRole, RoleMenu, User, Menu
from app.utils.ResponseWrap import successResponseWrap, failResponseWrap
from app.utils.GenerateMenus import generateMenuTree, filterMenuTree
from app.modules.VerifyAuth import role_required, permission_required

menu = Blueprint('menu', __name__)


# 获取菜单
@menu.get("/menus")
@jwt_required()
def menus():
    userId = get_jwt_identity()

    db_menus = db.session.query(Menu).select_from(UserRole) \
        .join(RoleMenu, UserRole.role_id == RoleMenu.role_id) \
        .join(Menu, RoleMenu.menu_id == Menu.id) \
        .join(User, UserRole.user_id == User.userId) \
        .filter(User.userId == userId, Menu.type != 2, Menu.hidden == 0, RoleMenu.deleted == 0).all()

    menus = [menu.to_json() for menu in db_menus]

    # 生成树形菜单
    menuTree = generateMenuTree(menus, 0)

    # 过滤菜单
    menuList = filterMenuTree(menuTree)

    return successResponseWrap(data=menuList)


# 获取菜单信息
@menu.get("/menu/info")
@permission_required("menu-read")
def getMenuInfo():
    permissionId = request.args.get("permissionId")

    db_menu = Menu.query.filter_by(id=permissionId).first()

    menuData = {
        "id": db_menu.id,
        "name": db_menu.name,
        "title": db_menu.title,
        "path": db_menu.path,
        "redirect": db_menu.redirect,
        "hidden": db_menu.hidden,
        "type": db_menu.type,
        "component": db_menu.component,
        "icon": db_menu.icon,
        "sort": db_menu.sort,
        "pid": db_menu.pid
    }

    return successResponseWrap(data=menuData)
