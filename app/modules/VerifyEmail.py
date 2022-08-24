# !/usr/bin/env python
# -*-coding: utf-8 -*-

from app.utils.ConnectionRedis import redisConnection
from app.utils.ResponseWrap import failResponseWrap


# 效验验证码
def verifyEmail(email, code):
    redis1 = redisConnection(1)

    # 检查验证码是否过期
    if not redis1.exists(email):
        return failResponseWrap(2007, "验证码已失效，请重新重新获取")

    if code != redis1.get(email):
        return failResponseWrap(2008, "验证码错误，请重新填写")

    # 验证成功则删除缓存的验证码
    redis1.delete(email)

    return True
