# !/usr/bin/env python
# -*-coding: utf-8 -*-
"""
# @File    : JWTLoader.py
# @Time    : 2022/7/10 23:08
# @Author  : Shuai
# @Email   : ls12345666@qq.com
"""
from flask_jwt_extended import JWTManager

from app.utils.ResponseWrap import failResponseWrap

# 实例化JWT
jwt = JWTManager()


# 重新定义Token回调错误内容
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return failResponseWrap(3002, "access_token过期")


@jwt.invalid_token_loader
def invalid_token_callback(jwt_header, jwt_payload):
    return failResponseWrap(3005, "非法token")
