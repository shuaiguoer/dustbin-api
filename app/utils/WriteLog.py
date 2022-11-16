# !/usr/bin/env python
# -*-coding: utf-8 -*-
import time

import requests
from user_agents import parse

from app import db
from app.models import LoginLog, OperationLog


def formatUserAgent(user_agent):
    user_agent = str(parse(str(user_agent)))
    user_agent_list = user_agent.split(" / ")

    device = user_agent_list[0]
    os = user_agent_list[1]
    browser = user_agent_list[2]

    return device, os, browser


def ip_to_location(ipaddr: str):
    if ipaddr.startswith("192.168") or ipaddr == "127.0.0.1" or ipaddr == 'localhost':
        return "局域网"

    url = f"http://api.map.baidu.com/location/ip?ak=1WW3aYc0HOT7ifIdxFy8OIUSWYpIFLWw&ip={ipaddr}&coor=bd09ll"
    resp = requests.get(url=url).json()
    status_code = resp["status"]
    if status_code:
        return str(resp)
    return resp["content"]["address"]


# 获取用户登录信息
def getUserLoginInfo(username, request):
    # 获取IP地址
    if request.headers.get("X-Forwarded-For"):
        ipaddr = request.headers.get("X-Forwarded-For")
    else:
        ipaddr = request.remote_addr

    # 获取客户端信息
    location = ip_to_location(ipaddr)
    device, os, browser = formatUserAgent(request.user_agent)
    login_time = int(round(time.time() * 1000))

    return {"username": username, "ipaddr": ipaddr, "location": location, "browser": browser, "os": os,
            "device": device, "login_time": login_time}


# 登录日志
def writeLoginLog(username, status, msg, request):
    # 获取IP地址
    if request.headers.get("X-Forwarded-For"):
        ipaddr = request.headers.get("X-Forwarded-For")
    else:
        ipaddr = request.remote_addr

    # 获取客户端信息
    location = ip_to_location(ipaddr)
    device, os, browser = formatUserAgent(request.user_agent)
    login_time = int(round(time.time() * 1000))

    # 跳过测试环境登录日志记录
    # if not ipaddr.startswith("192.168"):
    logInfo = LoginLog(username=username, ipaddr=ipaddr, location=location, browser=browser, os=os, device=device,
                       status=status, msg=msg, login_time=login_time)

    db.session.add(logInfo)

    db.session.commit()

    return {"username": username, "ipaddr": ipaddr, "location": location, "browser": browser, "os": os,
            "device": device, "status": status, "msg": msg, "login_time": login_time}


# 操作日志
def writeOperationLog(username, systemModule, operationType, status, returnParam, request):
    # 获取IP地址
    if request.headers.get("X-Forwarded-For"):
        ipaddr = request.headers.get("X-Forwarded-For")
    else:
        ipaddr = request.remote_addr

    # 获取日志信息
    location = ip_to_location(ipaddr)
    requestMethod = request.method
    requestPath = request.path
    requestParam = str(request.json)
    returnParam = str(returnParam)
    operation_time = int(round(time.time() * 1000))

    operationInfo = OperationLog(username=username, systemModule=systemModule, operationType=operationType,
                                 requestMethod=requestMethod, ipaddr=ipaddr, location=location, status=status,
                                 requestPath=requestPath, requestParam=requestParam, returnParam=returnParam,
                                 operation_time=operation_time)

    db.session.add(operationInfo)

    db.session.commit()

    return True
