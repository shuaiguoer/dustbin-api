# !/usr/bin/env python
# -*-coding: utf-8 -*-
"""
# @File    : role.py
# @Time    : 2022/7/13 14:58
# @Author  : Shuai
# @Email   : ls12345666@qq.com
"""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from app import db
from app.models import Role, Menu, RoleMenu
from app.utils.ResponseWrap import successResponseWrap
from app.modules.VerifyAuth import role_required, permission_required
from app.utils.GenerateMenus import generateMenuTree, filterRoleTree

role = Blueprint('role', __name__)


# 获取角色列表
@role.get("/role/list")
@permission_required("role-list")
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


# 获取角色的所有权限列表
@role.get("/role/permissions")
@permission_required("role-read")
def getRolePermissionList():
    db_menu = db.session.query(Menu.id, Menu.title, Menu.pid).all()

    menuList = []
    for menu in db_menu:
        menuList.append({
            "key": menu[0],
            "label": menu[1],
            "pid": menu[2]
        })

    menuTree = generateMenuTree(menuList, 0, "key")
    permissionList = filterRoleTree(menuTree)

    return successResponseWrap(data=permissionList)


# 获取角色信息
@role.get("/role/info")
@permission_required("role-read")
def getRoleInfo():
    roleId = request.args.get("roleId", type=int)

    # 有查询参数: 查询指定角色的所有权限ID列表
    db_menu_id = db.session.query(RoleMenu.menu_id).filter_by(role_id=roleId, deleted=0).all()
    menuList = [m[0] for m in db_menu_id]

    # 查询角色基本信息
    db_role = Role.query.filter_by(id=roleId).first()

    permissionData = {
        "roleId": roleId,
        "roleName": db_role.nickname,
        "description": db_role.description,
        "permissionIds": menuList,
    }

    return successResponseWrap(data=permissionData)


# 更新角色信息
@role.put("/role/update")
@permission_required("role-update")
def updateRole():
    roleId = request.json.get("roleId")
    roleName = request.json.get("roleName")
    description = request.json.get("description")
    permissionIds = set(request.json.get("permissionIds"))

    # 更新角色信息
    Role.query.filter_by(id=roleId).update({"nickname": roleName, "description": description})

    # 查询角色菜单
    db_role_menu = db.session.query(RoleMenu.menu_id).filter_by(role_id=roleId, deleted=0).all()
    db_permissionIds = set([mid[0] for mid in db_role_menu])

    # 更新角色菜单关系(删除)
    deleteList = db_permissionIds - permissionIds
    for delete_id in deleteList:
        RoleMenu.query.filter(RoleMenu.role_id == roleId, RoleMenu.menu_id == delete_id).update({"deleted": 1})

    # 更新角色菜单关系(新增)
    insertList = permissionIds - db_permissionIds
    for insert_id in insertList:
        db.session.add(RoleMenu(role_id=roleId, menu_id=insert_id))

    db.session.commit()

    return successResponseWrap("更新成功")


# 添加角色
@role.post("/role/add")
@permission_required("role-add")
def addRole():
    roleName = request.json.get("roleName")
    description = request.json.get("description")
    permissionIds = request.json.get("permissionIds")

    # 添加角色信息
    roleInfo = Role(nickname=roleName, description=description)
    db.session.add(roleInfo)

    db.session.flush()

    permissionObj = [RoleMenu(role_id=roleInfo.id, menu_id=mid) for mid in permissionIds]

    db.session.add_all(permissionObj)

    db.session.commit()

    return successResponseWrap("添加成功")


# 删除角色
@role.delete("/role/delete")
@permission_required("role-delete")
def deleteRole():
    roleId = request.json.get("roleId")

    # 删除角色菜单关系
    RoleMenu.query.filter_by(role_id=roleId).delete()

    # 删除角色
    Role.query.filter_by(id=roleId).delete()

    db.session.commit()

    return successResponseWrap("删除成功")
