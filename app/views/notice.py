# !/usr/bin/env python
# -*-coding: utf-8 -*-
import time

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from app import db
from app.models import Notice, NoticeUser, User
from app.modules.VerifyAuth import permission_required
from app.utils.ResponseWrap import successResponseWrap, failResponseWrap
from app.utils.WriteLog import writeOperationLog

notice = Blueprint('notice', __name__)


# 获取公告列表
@notice.get("/notice/list")
@permission_required("notice:list")
def getNoticeList():
    page = request.args.get("page", type=int)
    pageSize = request.args.get("pageSize", type=int)
    title = request.args.get("title")
    sender_name = request.args.get("sender_name")

    filter_params = []
    if title:
        filter_params.append(Notice.title.like(f"%{title}%"))
    if sender_name:
        # 获取包含sender_name的用户ID列表
        db_user = db.session.query(User.userId).filter(User.username.like(f"%{sender_name}%")).all()
        userList = [u[0] for u in db_user]
        filter_params.append(Notice.sender_id.in_(userList))

    db_notice = db.session.query(Notice, User) \
        .join(User, Notice.sender_id == User.userId) \
        .filter(*filter_params) \
        .order_by(db.desc(Notice.created_at)) \
        .limit(pageSize).offset(pageSize * (page - 1)) \
        .all()

    noticeList = []

    for n in db_notice:
        noticeList.append({
            "noticeId": n[0].id,
            "title": n[0].title,
            "content": n[0].content,
            "status": n[0].status,
            "sender_name": n[1].username,
            "created_at": n[0].created_at,
        })

    # 查询总数量
    itemCount = db.session.query(db.func.count(Notice.id)).filter(*filter_params).scalar()

    # 获取总页数
    pageCount = int((itemCount + pageSize - 1) / pageSize)

    noticeData = {
        "list": noticeList,
        "page": page,
        "pageSize": pageSize,
        "pageCount": pageCount,
        "itemCount": itemCount,
    }

    return successResponseWrap(data=noticeData)


# 获取公告信息
@notice.get("/notice/info")
@permission_required("notice:read")
def getNoticeInfo():
    noticeId = request.args.get("noticeId", type=int)

    db_notice = Notice.query.filter(Notice.id == noticeId).first()

    noticeData = {
        'noticeId': db_notice.id,
        'title': db_notice.title,
        'content': db_notice.content,
        'status': db_notice.status,
        'sender_id': db_notice.sender_id,
        'created_at': int(db_notice.created_at),
    }
    return successResponseWrap(data=noticeData)


# 添加公告
@notice.post("/notice/add")
@permission_required("notice:add")
def addNotice():
    sender_id = get_jwt_identity()
    title = request.json.get("title")
    content = request.json.get("content")
    created_at = int(round(time.time() * 1000))

    claims = get_jwt()
    myName = claims["username"]

    # 保存到公告数据库
    noticeInfo = Notice(title=title, content=content, sender_id=sender_id, created_at=created_at, status=1)
    db.session.add(noticeInfo)

    db.session.flush()

    notice_id = noticeInfo.id

    # 获取所有用户ID
    db_user = db.session.query(User.userId).all()
    userIds = [u[0] for u in db_user]

    # 保存到要发送到的公告关系表
    noticeObjList = []
    for i in userIds:
        noticeObjList.append(NoticeUser(notice_id=notice_id, recipient_id=i, created_at=created_at))

    db.session.add_all(noticeObjList)

    db.session.commit()

    successResponse = successResponseWrap("添加成功")

    # 记录日志
    writeOperationLog(username=myName, systemModule="添加公告", operationType=1, status=0, returnParam=successResponse,
                      request=request)

    return successResponse


# 更新/发布公告
@notice.put("/notice/update")
@permission_required("notice:update")
def updateNotice():
    noticeId = request.json.get("noticeId")
    title = request.json.get("title")
    content = request.json.get("content")

    claims = get_jwt()
    myName = claims["username"]

    # 判断更新对象是公告还是草稿
    db_notice = Notice.query.filter(Notice.id == noticeId).first()

    # 如果是草稿(2), 则发布
    if db_notice.status == 2:
        db_users = db.session.query(User.userId).all()
        userIds = [u[0] for u in db_users]

        # 保存到要发送到的公告关系表
        created_at = int(round(time.time() * 1000))
        noticeObjList = []
        for i in userIds:
            noticeObjList.append(NoticeUser(notice_id=noticeId, recipient_id=i, created_at=created_at))

        db.session.add_all(noticeObjList)

    # 更新公告基本信息
    Notice.query.filter(Notice.id == noticeId).update({"title": title, "content": content, "status": 1})

    db.session.commit()

    successResponse = successResponseWrap("更新成功")

    # 记录日志
    writeOperationLog(username=myName, systemModule="更新公告", operationType=2, status=0, returnParam=successResponse,
                      request=request)

    return successResponse


# 删除公告
@notice.delete("/notice/delete")
@permission_required("notice:delete")
def deleteNotice():
    noticeId = request.json.get("noticeId")

    claims = get_jwt()
    myName = claims["username"]

    noticeUserParams = []
    noticeParams = []

    if isinstance(noticeId, list):
        noticeUserParams.append(NoticeUser.notice_id.in_(noticeId))
        noticeParams.append(Notice.id.in_(noticeId))
    else:
        noticeUserParams.append(NoticeUser.notice_id == noticeId)
        noticeParams.append(Notice.id == noticeId)

    # 删除公告用户关系
    NoticeUser.query.filter(*noticeUserParams).delete()

    # 删除公告基本信息
    result = Notice.query.filter(*noticeParams).delete()

    if not result:
        return failResponseWrap(5001, "未找到您要删除的公告")

    db.session.commit()

    successResponse = successResponseWrap("删除成功")

    # 记录日志
    writeOperationLog(username=myName, systemModule="删除公告", operationType=3, status=0, returnParam=successResponse,
                      request=request)

    return successResponse


# 获取我的公告列表
@notice.get("/notice/own/list")
@jwt_required()
def getNoticeOwnList():
    userId = get_jwt_identity()
    page = request.args.get("page", type=int)
    pageSize = request.args.get("pageSize", type=int)

    db_notice = db.session.query(NoticeUser, Notice, User) \
        .join(Notice) \
        .join(User, Notice.sender_id == User.userId) \
        .filter(NoticeUser.recipient_id == userId, NoticeUser.deleted == 0) \
        .order_by(db.desc(Notice.created_at)) \
        .limit(pageSize).offset(pageSize * (page - 1)) \
        .all()

    noticeList = []

    for n in db_notice:
        noticeList.append({
            "noticeId": n[1].id,
            "title": n[1].title,
            "content": n[1].content,
            "sender_id": n[1].sender_id,
            "sender_name": n[2].username,
            "created_at": n[1].created_at,
            "state": n[0].state,
        })

    itemCount = db.session.query(db.func.count(NoticeUser.id)) \
        .filter(NoticeUser.recipient_id == userId, NoticeUser.deleted == 0, NoticeUser.state == 0) \
        .scalar()

    # 获取总页数
    pageCount = int((itemCount + pageSize - 1) / pageSize)

    qrcodeData = {
        "list": noticeList,
        "page": page,
        "pageSize": pageSize,
        "pageCount": pageCount,
        "itemCount": itemCount,
    }

    return successResponseWrap(data=qrcodeData)


# 设置公告读取状态
@notice.put("/notice/set/read-state")
@jwt_required()
def setNoticeReadState():
    userId = get_jwt_identity()
    noticeId = request.json.get("noticeId")
    state = request.json.get("state")
    allRead = request.json.get("allRead")
    read_time = int(round(time.time() * 1000))

    if allRead:
        result = NoticeUser.query.filter(NoticeUser.recipient_id == userId).update({"state": 1, "read_time": read_time})
    else:
        result = NoticeUser.query.filter(NoticeUser.recipient_id == userId, NoticeUser.notice_id == noticeId) \
            .update({"state": state, "read_time": read_time})

    if not result:
        return failResponseWrap(5001, "未找到您要设置读取状态的公告")

    db.session.commit()

    return successResponseWrap(f"设置成功")


# 获取公告阅读状态列表
@notice.get("/notice/state/list")
@permission_required("notice:list")
def getNoticeReadStateList():
    noticeId = request.args.get("noticeId", type=int)
    page = request.args.get("page", type=int)
    pageSize = request.args.get("pageSize", type=int)

    db_notice_user = db.session.query(NoticeUser, User) \
        .join(User) \
        .filter(NoticeUser.notice_id == noticeId) \
        .limit(pageSize).offset(pageSize * (page - 1)) \
        .all()

    noticeReadStateList = []

    for notice_user in db_notice_user:
        noticeReadStateList.append({
            "recipient": notice_user[1].username,
            "state": notice_user[0].state,
            "readTime": notice_user[0].read_time,
        })

    # 查询总数量
    itemCount = db.session.query(db.func.count(NoticeUser.id)).filter(NoticeUser.notice_id == noticeId).scalar()

    # 获取总页数
    pageCount = int((itemCount + pageSize - 1) / pageSize)

    noticeReadStateData = {
        "list": noticeReadStateList,
        "page": page,
        "pageSize": pageSize,
        "pageCount": pageCount,
        "itemCount": itemCount,
    }

    return successResponseWrap(data=noticeReadStateData)


# 保存公告为草稿
@notice.post("/notice/draft/save")
@permission_required("notice:add")
def saveNoticeDraft():
    sender_id = get_jwt_identity()
    noticeId = request.json.get("noticeId")
    title = request.json.get("title")
    content = request.json.get("content")
    created_at = int(round(time.time() * 1000))

    claims = get_jwt()
    myName = claims["username"]

    # 保存到公告数据库
    # 如果不是第一次保存草稿: 更新
    if noticeId:
        Notice.query.filter(Notice.id == noticeId).update({"title": title, "content": content})
    else:
        # 否则: 添加
        db.session.add(Notice(title=title, content=content, sender_id=sender_id, created_at=created_at, status=2))

    db.session.commit()

    successResponse = successResponseWrap("草稿保存成功")

    # 记录日志
    writeOperationLog(username=myName, systemModule="保存消息草稿", operationType=1, status=0,
                      returnParam=successResponse,
                      request=request)

    return successResponse
