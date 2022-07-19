# !/usr/bin/env python
# -*-coding: utf-8 -*-
"""
# @File    : VerifyAuth.py
# @Time    : 2022/7/13 22:25
# @Author  : Shuai
# @Email   : ls12345666@qq.com
"""
from functools import wraps

from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity

from app import db
from app.models import UserRole, RoleMenu, User, Menu, Role
from app.utils.ResponseWrap import failResponseWrap
from app.conf.StatusCode import PERMISSION_NO_ACCESS


# 角色鉴定
def role_required(*roles_need):
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()

            userId = get_jwt_identity()

            db_role = Role.query.join(UserRole).filter_by(user_id=userId).first()
            role = db_role.name

            if not roles_need:
                if role not in ('admin',):
                    return failResponseWrap(*PERMISSION_NO_ACCESS)
            else:
                if role not in roles_need:
                    return failResponseWrap(*PERMISSION_NO_ACCESS)
            return fn(*args, **kwargs)

        return decorator

    return wrapper


# 权限鉴定
def permission_required(*permissions_need):
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()

            userId = get_jwt_identity()

            db_permissions = db.session.query(Menu.name).select_from(UserRole) \
                .join(RoleMenu, UserRole.role_id == RoleMenu.role_id) \
                .join(Menu, Menu.id == RoleMenu.menu_id) \
                .filter(Menu.type == 2, RoleMenu.deleted == 0, UserRole.user_id == userId).all()

            if permissions_need not in db_permissions:
                return failResponseWrap(*PERMISSION_NO_ACCESS)
            return fn(*args, **kwargs)

        return decorator

    return wrapper
