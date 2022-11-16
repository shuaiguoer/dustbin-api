# !/usr/bin/env python
# -*-coding: utf-8 -*-
from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from app import db
from app.models import LoginLog, OperationLog
from app.modules.VerifyAuth import permission_required
from app.utils.ResponseWrap import successResponseWrap, failResponseWrap
from app.utils.WriteLog import ip_to_location

log = Blueprint('log', __name__)


# 获取登录日志列表
@log.get("/log/login/list")
@permission_required("log:list")
def getLoginLogList():
    ipaddr = request.args.get("ipaddr")
    username = request.args.get("username")
    status = request.args.get("status")
    login_time = request.args.getlist("login_time[]")
    page = request.args.get("page", type=int)
    pageSize = request.args.get("pageSize", type=int)

    filter_params = []
    if ipaddr:
        filter_params.append(LoginLog.ipaddr.like(f"%{ipaddr}%"))
    if username:
        filter_params.append(LoginLog.username.like(f"%{username}%"))
    if status:
        filter_params.append(LoginLog.status == status)
    if login_time:
        filter_params.append(LoginLog.login_time.between(*login_time))

    db_logs = LoginLog.query.filter(*filter_params) \
        .order_by(db.desc(LoginLog.login_time)) \
        .limit(pageSize).offset(pageSize * (page - 1)) \
        .all()

    logList = []

    for i in db_logs:
        logList.append({
            "logId": i.id,
            "username": i.username,
            "ipaddr": i.ipaddr,
            "location": i.location,
            "browser": i.browser,
            "os": i.os,
            "device": i.device,
            "status": i.status,
            "msg": i.msg,
            "login_time": int(i.login_time)
        })

    # 查询总数量
    itemCount = db.session.query(db.func.count(LoginLog.id)).filter(*filter_params).scalar()

    # 获取总页数
    pageCount = int((itemCount + pageSize - 1) / pageSize)

    qrcodeData = {
        "list": logList,
        "page": page,
        "pageSize": pageSize,
        "pageCount": pageCount,
        "itemCount": itemCount,
    }

    return successResponseWrap(data=qrcodeData)


# 删除登录日志
@log.delete("/log/login/delete")
@permission_required("log:delete")
def deleteLoginLog():
    logIds = request.json.get("logIds")

    result = LoginLog.query.filter(LoginLog.id.in_(logIds)).delete()

    if not result:
        return failResponseWrap(5001, "未找到您要删除的日志")

    db.session.commit()

    return successResponseWrap("删除成功")


# 清空登录日志
@log.delete("/log/login/clear")
@permission_required("log:delete")
def clearLoginLog():
    result = LoginLog.query.delete()

    if not result:
        return failResponseWrap(5001, "日志不存在")

    db.session.commit()

    return successResponseWrap("已清空")


# 获取操作日志列表
@log.get("/log/operation/list")
@permission_required("log:list")
def getOperationLogList():
    systemModule = request.args.get("systemModule")
    username = request.args.get("username")
    operationType = request.args.get("operationType")
    status = request.args.get("status")
    operation_time = request.args.getlist("operation_time[]")
    page = request.args.get("page", type=int)
    pageSize = request.args.get("pageSize", type=int)

    filter_params = []
    if systemModule:
        filter_params.append(OperationLog.systemModule.like(f"%{systemModule}%"))
    if username:
        filter_params.append(OperationLog.username.like(f"%{username}%"))
    if operationType:
        filter_params.append(OperationLog.operationType == operationType)
    if status:
        filter_params.append(OperationLog.status == status)
    if operation_time:
        filter_params.append(OperationLog.login_time.between(*operation_time))

    db_logs = OperationLog.query.filter(*filter_params) \
        .order_by(db.desc(OperationLog.operation_time)) \
        .limit(pageSize).offset(pageSize * (page - 1)) \
        .all()

    logList = []

    for i in db_logs:
        logList.append({
            "logId": i.id,
            "username": i.username,
            "systemModule": i.systemModule,
            "operationType": str(i.operationType),
            "requestMethod": i.requestMethod,
            "ipaddr": i.ipaddr,
            "location": i.location,
            "status": i.status,
            "operation_time": int(i.operation_time)
        })

    # 查询总数量
    itemCount = db.session.query(db.func.count(OperationLog.id)).filter(*filter_params).scalar()

    # 获取总页数
    pageCount = int((itemCount + pageSize - 1) / pageSize)

    qrcodeData = {
        "list": logList,
        "page": page,
        "pageSize": pageSize,
        "pageCount": pageCount,
        "itemCount": itemCount,
    }

    return successResponseWrap(data=qrcodeData)


# 获取操作日志信息
@log.get("/log/operation/info")
@permission_required("log:list")
def getOperationLogInfo():
    logId = request.args.get("logId", type=int)

    db_log = OperationLog.query.filter(OperationLog.id == logId).first()

    logData = {
        "logId": db_log.id,
        "username": db_log.username,
        "systemModule": db_log.systemModule,
        "operationType": str(db_log.operationType),
        "requestMethod": db_log.requestMethod,
        "ipaddr": db_log.ipaddr,
        "location": db_log.location,
        "status": db_log.status,
        "requestPath": db_log.requestPath,
        "requestParam": db_log.requestParam,
        "returnParam": db_log.returnParam,
        "operation_time": int(db_log.operation_time)
    }

    return successResponseWrap(data=logData)


# 删除登录日志
@log.delete("/log/operation/delete")
@permission_required("log:delete")
def deleteOperationLog():
    logIds = request.json.get("logIds")

    result = OperationLog.query.filter(OperationLog.id.in_(logIds)).delete()

    if not result:
        return failResponseWrap(5001, "未找到您要删除的日志")

    db.session.commit()

    return successResponseWrap("删除成功")


# 清空登录日志
@log.delete("/log/operation/clear")
@permission_required("log:delete")
def clearOperationLog():
    result = OperationLog.query.delete()

    if not result:
        return failResponseWrap(5001, "日志不存在")

    db.session.commit()

    return successResponseWrap("已清空")


# 添加操作日志
@log.post("/log/operation/add")
@jwt_required()
def addOperationLog():
    username = request.json.get("username")
    systemModule = request.json.get("systemModule")
    operationType = request.json.get("operationType")
    requestMethod = request.json.get("requestMethod")
    ipaddr = request.json.get("ipaddr")
    status = request.json.get("status")
    requestPath = request.json.get("requestPath")
    requestParam = request.json.get("requestParam")
    returnParam = request.json.get("returnParam")
    operation_time = request.json.get("operation_time")

    location = ip_to_location(ipaddr)

    operationInfo = OperationLog(username=username, systemModule=systemModule, operationType=operationType,
                                 requestMethod=requestMethod, ipaddr=ipaddr, location=location, status=status,
                                 requestPath=requestPath, requestParam=requestParam, returnParam=returnParam,
                                 operation_time=operation_time)

    db.session.add(operationInfo)

    db.session.commit()

    return successResponseWrap("添加成功")
