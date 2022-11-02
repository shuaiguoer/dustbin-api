# !/usr/bin/env python3
# -*-coding: utf-8 -*-
"""
# @File    : menuController.py
# @Time    : 2022/7/10 17:09
# @Author  : Shuai
# @Email   : ls12345666@qq.com
"""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from app.models import UserRole, RoleMenu, User, Menu, Dict, DictItem
from app.modules.VerifyAuth import permission_required
from app.utils.GenerateMenus import generateMenuTree, filterMenuTree
from app.utils.ResponseWrap import successResponseWrap, failResponseWrap

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
        .filter(User.userId == userId, RoleMenu.deleted == 0, Menu.type != 2, Menu.disabled == 0) \
        .all()

    menus = [menu.to_dict() for menu in db_menus]

    # 生成树形菜单
    menuTree = generateMenuTree(menus, 0)

    # 过滤菜单
    menuList = filterMenuTree(menuTree)

    dictData = {}
    db_dict = Dict.query.all()
    dictTypeList = [d.type for d in db_dict]

    for dt in dictTypeList:
        db_dictItem = DictItem.query.join(Dict, DictItem.dict_id == Dict.id).filter(Dict.type == dt).all()
        dictData[dt] = [d.to_dict() for d in db_dictItem]

    data = {
        "menuList": menuList,
        "dictData": dictData
    }

    return successResponseWrap(data=data)


# 获取菜单列表
@menu.get("/menu/list")
@permission_required("menu:list")
def getRolePermissionList():
    db_menu = Menu.query.order_by(db.asc(Menu.sort)).all()

    menuList = [m.to_dict() for m in db_menu]
    menuTree = generateMenuTree(menuList, 0)

    return successResponseWrap(data={"list": menuTree})


# 获取菜单信息
@menu.get("/menu/info")
@permission_required("menu:read")
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
        "disabled": db_menu.disabled,
        "type": db_menu.type,
        "component": db_menu.component,
        "icon": db_menu.icon,
        "sort": db_menu.sort,
        "pid": db_menu.pid
    }

    return successResponseWrap(data=menuData)


# 更新菜单信息
@menu.put("/menu/update")
@permission_required("menu:update")
def updateMenu():
    menuId = request.json.get("id")
    name = request.json.get("name")
    title = request.json.get("title")
    path = request.json.get("path")
    redirect = request.json.get("redirect")
    hidden = request.json.get("hidden")
    disabled = request.json.get("disabled")
    menuType = request.json.get("type")
    component = request.json.get("component")
    icon = request.json.get("icon")
    sort = request.json.get("sort")
    pid = request.json.get("pid")

    result = Menu.query.filter_by(id=menuId) \
        .update({"name": name, "title": title, "path": path, "redirect": redirect, "hidden": hidden,
                 "disabled": disabled, "type": menuType, "component": component, "icon": icon, "sort": sort,
                 "pid": pid})

    if not result:
        return failResponseWrap(5001, "没有数据被更新")

    db.session.commit()

    return successResponseWrap("更新成功")


# 删除菜单
@menu.delete("/menu/delete")
@permission_required("menu:delete")
def deleteMenu():
    menuId = request.json.get("menuId")

    # 删除角色菜单关系
    RoleMenu.query.filter_by(menu_id=menuId).delete()

    # 删除菜单
    result = Menu.query.filter_by(id=menuId).delete()

    if not result:
        return failResponseWrap(5001, "未找到您要删除的菜单")

    db.session.commit()

    return successResponseWrap("删除成功")


# 添加菜单
@menu.post("/menu/add")
@permission_required("menu:add")
def addMenu():
    name = request.json.get("name")
    title = request.json.get("title")
    path = request.json.get("path") or ''
    redirect = request.json.get("redirect") or ''
    hidden = request.json.get("hidden")
    disabled = request.json.get("disabled")
    menuType = request.json.get("type")
    component = request.json.get("component") or ''
    icon = request.json.get("icon")
    sort = request.json.get("sort")
    pid = request.json.get("pid")

    menuInfo = Menu(name=name, title=title, path=path, redirect=redirect, hidden=hidden, disabled=disabled,
                    type=menuType, component=component, icon=icon, sort=sort, pid=pid)
    db.session.add(menuInfo)

    db.session.commit()

    return successResponseWrap("添加成功")
