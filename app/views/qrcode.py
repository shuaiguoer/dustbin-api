# !/usr/bin/env python
# -*-coding: utf-8 -*-
# !/usr/bin/env python
# -*-coding: utf-8 -*-
import time

from flask import Blueprint, request, redirect, abort

from app import db
from app.models import Qrcode
from app.modules.VerifyAuth import permission_required
from app.utils.ResponseWrap import successResponseWrap, failResponseWrap

qrcode = Blueprint('qrcode', __name__)


# 动态二维码
@qrcode.get("/qr/<source>")
def qrcodeDynamic(source):
    # 判断数据库中是否存在跳转数据
    db_qrcode = Qrcode.query.filter_by(source=source, deleted=0).first()

    if not db_qrcode:
        abort(404)

    return redirect(db_qrcode.target)


# 获取动态二维码列表
@qrcode.get("/qrcode/list")
@permission_required("qrcode:list")
def getQrcodeList():
    page = request.args.get("page", type=int, default=1)
    pageSize = request.args.get("pageSize", type=int, default=10)
    source = request.args.get("source")
    target = request.args.get("target")
    description = request.args.get("description")

    params = []
    if source:
        params.append(Qrcode.source.like(f'%{source}%'))
    if target:
        params.append(Qrcode.target.like(f'%{target}%'))
    if description:
        params.append(Qrcode.description.like(f'%{description}%'))

    db_qrcodes = Qrcode.query.filter(*params).limit(pageSize).offset(pageSize * (page - 1)).all()

    qrcodeList = [qr.to_dict() for qr in db_qrcodes]

    # 查询角色总数量
    itemCount = db.session.query(db.func.count(Qrcode.id)).filter(*params).scalar()

    # 获取总页数
    pageCount = int((itemCount + pageSize - 1) / pageSize)

    qrcodeData = {
        "list": qrcodeList,
        "page": page,
        "pageSize": pageSize,
        "pageCount": pageCount,
        "itemCount": itemCount,
    }

    return successResponseWrap(data=qrcodeData)


# 获取动态二维码信息
@qrcode.get("/qrcode/info")
@permission_required("qrcode:read")
def getQrcodeInfo():
    qrcodeId = request.args.get("qrcodeId", type=int)

    db_qrcode = Qrcode.query.filter_by(id=qrcodeId).first()

    qrcodeData = {
        "qrcodeId": db_qrcode.id,
        "source": db_qrcode.source,
        "target": db_qrcode.target,
        "description": db_qrcode.description,
        "updated_at": db_qrcode.updated_at,
        "deleted": db_qrcode.deleted
    }

    return successResponseWrap(data=qrcodeData)


# 添加动态二维码
@qrcode.post("/qrcode/add")
@permission_required("qrcode:add")
def addQrcode():
    source = request.json.get("source")
    target = request.json.get("target")
    description = request.json.get("description")
    deleted = request.json.get("deleted")
    updated_at = int(round(time.time() * 1000))

    # 判断源地址是否有重复
    db_qrcode = Qrcode.query.filter_by(source=source).first()
    if db_qrcode:
        return failResponseWrap(1001, "该源地址已存在, 请修改源地址后重试")

    db.session.add(
        Qrcode(source=source, target=target, description=description, deleted=deleted, updated_at=updated_at))

    db.session.commit()

    return successResponseWrap("添加成功")


# 更新动态二维码
@qrcode.put("/qrcode/update")
@permission_required("qrcode:update")
def updateQrcode():
    qrcodeId = request.json.get("qrcodeId")
    source = request.json.get("source")
    target = request.json.get("target")
    description = request.json.get("description")
    deleted = request.json.get("deleted")
    updated_at = int(round(time.time() * 1000))

    result = Qrcode.query.filter_by(id=qrcodeId).update(
        {"source": source, "target": target, "description": description, "deleted": deleted, "updated_at": updated_at})

    if not result:
        return failResponseWrap(5001, "未找到您要更新的二维码")

    db.session.commit()

    return successResponseWrap("二维码更新成功")


# 删除动态二维码
@qrcode.delete("/qrcode/delete")
@permission_required("qrcode:delete")
def deleteQrcode():
    qrcodeId = request.json.get("qrcodeId")

    result = Qrcode.query.filter_by(id=qrcodeId).delete()

    if not result:
        return failResponseWrap(5001, "未找到您要删除的二维码")

    db.session.commit()

    return successResponseWrap("删除成功")
