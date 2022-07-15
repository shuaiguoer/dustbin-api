# !/usr/bin/env python
# -*-coding: utf-8 -*-
"""
# @File    : ConnectionRedis.py.py
# @Time    : 2022/7/15 23:22
# @Author  : Shuai
# @Email   : ls12345666@qq.com
"""
import redis

from flask import current_app


def redisConnection(db):
    pool = redis.ConnectionPool(host=current_app.config.get('REDIS_HOST'), port=current_app.config.get('REDIS_PORT'),
                                password=current_app.config.get('REDIS_PASSWORD'), db=db, decode_responses=True)
    return redis.Redis(connection_pool=pool)
