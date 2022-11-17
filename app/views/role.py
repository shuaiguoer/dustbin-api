# !/usr/bin/env python
# -*-coding: utf-8 -*-
"""
# @File    : role.py
# @Time    : 2022/7/13 14:58
# @Author  : Shuai
# @Email   : ls12345666@qq.com
"""
from flask import Blueprint, request
from flask_jwt_extended import get_jwt

from app import db
from app.models import Role, Menu, RoleMenu, UserRole
from app.modules.VerifyAuth import permission_required
from app.utils.GenerateMenus import generateMenuTree, filterRoleTree
from app.utils.ResponseWrap import successResponseWrap, failResponseWrap
from app.utils.WriteLog import writeOperationLog

role = Blueprint('role', __name__)


# 获取角色列表
@role.get("/role/list")
@permission_required("role:list")
def getRoleList():
    page = request.args.get("page", type=int)
    pageSize = request.args.get("pageSize", type=int)

    # 查询所有角色
    roles = Role.query.order_by(db.asc(Role.sort)).slice(pageSize * (page - 1), pageSize * page).all()

    roleList = [r.to_dict() for r in roles]

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


# 获取角色信息
@role.get("/role/info")
@permission_required("role:read")
def getRoleInfo():
    roleId = request.args.get("roleId", type=int)

    # 查询角色基本信息
    db_role = Role.query.filter_by(id=roleId).first()

    roleData = {
        "roleId": roleId,
        "roleName": db_role.name,
        "roleNickName": db_role.nickname,
        "description": db_role.description,
        "sort": db_role.sort,
    }

    return successResponseWrap(data=roleData)


# 更新角色信息
@role.put("/role/update")
@permission_required("role:update")
def updateRole():
    roleId = request.json.get("roleId")
    roleName = request.json.get("roleName")
    roleNickName = request.json.get("roleNickName")
    description = request.json.get("description")
    sort = request.json.get("sort")

    claims = get_jwt()
    myName = claims["username"]

    # 更新角色信息
    Role.query.filter_by(id=roleId) \
        .update({"name": roleName, "nickname": roleNickName, "description": description, "sort": sort})

    db.session.commit()

    # 记录日志
    successResponse = successResponseWrap("更新成功")
    writeOperationLog(username=myName, systemModule="更新角色", operationType=2, status=0, returnParam=successResponse,
                      request=request)

    return successResponse


# 添加角色
@role.post("/role/add")
@permission_required("role:add")
def addRole():
    roleName = request.json.get("roleName")
    roleNickName = request.json.get("roleNickName")
    description = request.json.get("description")
    sort = request.json.get("sort")

    claims = get_jwt()
    myName = claims["username"]

    # 添加角色信息
    roleInfo = Role(name=roleName, nickname=roleNickName, description=description, sort=sort)
    db.session.add(roleInfo)

    db.session.commit()

    successResponse = successResponseWrap("添加成功")

    # 记录日志
    writeOperationLog(username=myName, systemModule="添加角色", operationType=1, status=0, returnParam=successResponse,
                      request=request)

    return successResponseWrap("添加成功")


# 删除角色
@role.delete("/role/delete")
@permission_required("role:delete")
def deleteRole():
    roleId = request.json.get("roleId")

    claims = get_jwt()
    myName = claims["username"]

    # 删除角色与菜单的关系
    RoleMenu.query.filter_by(role_id=roleId).delete()

    # 将拥有该角色的用户全部设置为普通用户
    UserRole.query.filter_by(role_id=roleId).update({"role_id": 2})

    # 删除角色
    result = Role.query.filter_by(id=roleId).delete()

    if not result:
        return failResponseWrap(5001, "未找到您要删除的角色")

    db.session.commit()

    successResponse = successResponseWrap("删除成功")

    # 记录日志
    writeOperationLog(username=myName, systemModule="删除角色", operationType=3, status=0, returnParam=successResponse,
                      request=request)

    return successResponse


# 获取角色的所有权限列表
@role.get("/role/permissions/list")
@permission_required("role:read")
def getRolePermissionList():
    db_menu = db.session.query(Menu.id, Menu.title, Menu.pid).order_by(db.asc(Menu.sort)).all()

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


# 获取角色权限
@role.get("/role/permissions/info")
@permission_required("role-permissions:read")
def getRolePermissions():
    roleId = request.args.get("roleId", type=int)

    # 查询指定角色的所有权限ID列表
    db_menu_id = db.session.query(RoleMenu.menu_id).filter_by(role_id=roleId, deleted=0).all()
    permissionList = [m[0] for m in db_menu_id]

    # 获取所有菜单权限树
    menuList = []
    db_menu = db.session.query(Menu.id, Menu.title, Menu.pid).order_by(db.asc(Menu.sort)).all()
    for menu in db_menu:
        menuList.append({
            "key": menu[0],
            "label": menu[1],
            "pid": menu[2]
        })
    menuTree = generateMenuTree(menuList, 0, "key")

    # 获取所有子树ID
    ids = []

    def dfs(tree):
        if "children" not in tree:
            key = tree.get("key")
            if permissionList.count(key) == 1:
                ids.append(key)
            return
        for c in tree["children"]:
            dfs(c)

    for m in menuTree:
        dfs(m)

    return successResponseWrap(data=ids)


# 更新角色权限
@role.put("/role/permissions/update")
@permission_required("role-permissions:update")
def updateRolePermissions():
    roleId = request.json.get("roleId")
    permissionIds = set(request.json.get("permissionIds"))
    parentPermissionIds = set(request.json.get("parentPermissionIds"))

    claims = get_jwt()
    myName = claims["username"]

    # 合并菜单(权限)
    permissionIds = parentPermissionIds | permissionIds

    # 查询角色菜单
    db_role_menu = db.session.query(RoleMenu.menu_id).filter_by(role_id=roleId, deleted=0).all()
    db_permissionIds = set([mid[0] for mid in db_role_menu])

    # 更新角色菜单关系(删除)
    deleteList = db_permissionIds - permissionIds
    for delete_id in deleteList:
        RoleMenu.query.filter(RoleMenu.role_id == roleId, RoleMenu.menu_id == delete_id).update({"deleted": 1})

    # 更新角色菜单关系(修改: 有则更新, 无则新增)
    changeList = permissionIds - db_permissionIds
    if changeList:
        # 查询出当前已标记删除的菜单权限
        db_role_menu_deleted = db.session.query(RoleMenu.menu_id).filter_by(role_id=roleId, deleted=1).all()
        db_permissionIds_deleted = set([mid[0] for mid in db_role_menu_deleted])

        # 计算出需要更新的角色菜单关系
        updateList = permissionIds & db_permissionIds_deleted
        for update_id in updateList:
            RoleMenu.query.filter(RoleMenu.role_id == roleId, RoleMenu.menu_id == update_id).update({"deleted": 0})

        # 计算出需要新增的角色菜单关系
        insertList = changeList - updateList
        for insert_id in insertList:
            db.session.add(RoleMenu(role_id=roleId, menu_id=insert_id))

    db.session.commit()

    successResponse = successResponseWrap("角色权限更新成功")

    # 记录日志
    writeOperationLog(username=myName, systemModule="更新角色", operationType=2, status=0, returnParam=successResponse,
                      request=request)

    return successResponse
