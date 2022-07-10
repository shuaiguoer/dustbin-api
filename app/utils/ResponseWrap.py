# !/usr/bin/env python3
# -*-coding: utf-8 -*-
"""
# @File    : ResponseWrap.py
# @Time    : 2022/7/10 14:18
# @Author  : Shuai
# @Email   : ls12345666@qq.com
"""


# 成功响应体
def successResponseWrap(message: str = "请求成功", data=""):
    return {
        "code": 0,
        "message": message,
        "data": data,
    }


# 失败响应体
def failResponseWrap(code: int = 1, message: str = "请求失败", data=""):
    return {
        "code": code,
        "message": message,
        "data": data,
    }
