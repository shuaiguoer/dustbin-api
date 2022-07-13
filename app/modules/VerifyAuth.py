# !/usr/bin/env python
# -*-coding: utf-8 -*-
"""
# @File    : VerifyAuth.py
# @Time    : 2022/7/13 22:25
# @Author  : Shuai
# @Email   : ls12345666@qq.com
"""
from functools import wraps

from flask_jwt_extended import verify_jwt_in_request, get_jwt

from app.utils.ResponseWrap import failResponseWrap
from app.conf.StatusCode import PERMISSION_NO_ACCESS


# 角色鉴定
def role_required(*roles_need):
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            role = claims["role"]
            if not roles_need:
                if role not in ('admin',):
                    return failResponseWrap(*PERMISSION_NO_ACCESS)
            else:
                if role not in roles_need:
                    return failResponseWrap(*PERMISSION_NO_ACCESS)
            return fn(*args, **kwargs)

        return decorator

    return wrapper
