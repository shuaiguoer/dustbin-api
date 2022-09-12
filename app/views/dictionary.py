# !/usr/bin/env python
# -*-coding: utf-8 -*-
# !/usr/bin/env python
# -*-coding: utf-8 -*-

import time

from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from app import db
from app.models import Role, Dict, DictItem
from app.modules.VerifyAuth import permission_required
from app.utils.ResponseWrap import successResponseWrap, failResponseWrap

dictionary = Blueprint('dictionary', __name__)


# 获取字典列表
@dictionary.get("/dict/list")
@permission_required("dict:list")
def getDictList():
    page = request.args.get("page", type=int)
    pageSize = request.args.get("pageSize", type=int)
    dictName = request.args.get("dictName")

    filter_params = []
    if dictName:
        filter_params.append(Dict.name.like(f"%{dictName}%"))

    db_dict = Dict.query.filter(*filter_params).limit(pageSize).offset(pageSize * (page - 1)).all()

    dictList = []
    for d in db_dict:
        dictList.append({
            "key": d.id,
            "label": d.name,
            "type": d.type,
            "deleted": d.deleted,
            "description": d.description
        })

    # 查询字典总数量
    itemCount = db.session.query(db.func.count(Dict.id)).filter(*filter_params).scalar()

    # 获取总页数
    pageCount = int((itemCount + pageSize - 1) / pageSize)

    dictData = {
        "list": dictList,
        "page": page,
        "pageSize": pageSize,
        "pageCount": pageCount,
        "itemCount": itemCount,
    }

    return successResponseWrap(data=dictData)


# 更新字典
@dictionary.put("/dict/update")
@permission_required("dict:update")
def updateDict():
    key = request.json.get("key")
    label = request.json.get("label")
    dictType = request.json.get("type")
    deleted = request.json.get("deleted")
    description = request.json.get("description")

    db_dict = Dict.query.filter(Dict.type == dictType, Dict.id != key).first()
    if db_dict:
        return failResponseWrap(5003, f"更新失败, 已存在相同类字典类型: {db_dict.name}")

    result = Dict.query.filter_by(id=key) \
        .update({"name": label, "description": description, "type": dictType, "deleted": deleted})

    if not result:
        return failResponseWrap(5001, "字典更新失败")

    db.session.commit()

    return successResponseWrap("字典更新成功")


# 新增字典
@dictionary.post("/dict/add")
@permission_required("dict:add")
def addDict():
    label = request.json.get("label")
    dictType = request.json.get("type")
    deleted = request.json.get("deleted")
    description = request.json.get("description")

    db_dict = Dict.query.filter_by(type=dictType).first()
    if db_dict:
        return failResponseWrap(5003, f"添加失败, 已存在相同类字典类型: {db_dict.name}")

    dictInfo = Dict(name=label, type=dictType, deleted=deleted, description=description)
    db.session.add(dictInfo)

    db.session.commit()

    return successResponseWrap("字典添加成功")


# 删除字典
@dictionary.delete("/dict/delete")
@permission_required("dict:delete")
@jwt_required()
def deleteDict():
    dictId = request.json.get("dictId")

    # 获取字典包含的字典项ID
    db_dictItem = DictItem.query.filter_by(dict_id=dictId).all()
    dictItemIds = [d.id for d in db_dictItem]

    if dictItemIds:
        for di in dictItemIds:
            # 删除字典包含的字典项
            DictItem.query.filter_by(id=di).delete()

    # 删除字典
    result = Dict.query.filter_by(id=dictId).delete()

    if not result:
        return failResponseWrap(5001, "未找到该字典项, 删除字典失败")

    db.session.commit()

    return successResponseWrap("字典删除成功")


# 获取字典项列表
@dictionary.get("/dict-item/list")
@jwt_required()
def getDictItemList():
    dictTypeList = request.args.getlist("dictTypeList[]")
    dictType = request.args.getlist("dictType")
    dictItemName = request.args.get("dictItemName")
    page = request.args.get("page", type=int)
    pageSize = request.args.get("pageSize", type=int)

    dictData = {
        "list": [],
        "page": page,
        "pageSize": pageSize,
        "pageCount": None,
        "itemCount": None,
    }

    db_dict = []
    if dictTypeList:
        db_dict = Dict.query.filter(Dict.type.in_(dictTypeList)).all()
    elif dictType:
        db_dict = Dict.query.filter(Dict.type == dictType).all()

    if not db_dict:
        return successResponseWrap(dictData)

    dictIds = [d.id for d in db_dict]

    filter_params = []
    if dictItemName:
        filter_params.append(DictItem.label.like(f'%{dictItemName}%'))

    db_dictItem = DictItem.query \
        .filter(DictItem.dict_id.in_(dictIds), *filter_params) \
        .limit(pageSize).offset(pageSize * (page - 1)) \
        .all()

    # 查询字典总数量
    dictData["itemCount"] = db.session.query(db.func.count(DictItem.id)) \
        .filter(DictItem.dict_id.in_(dictIds), *filter_params).scalar()

    # 获取总页数
    dictData["pageCount"] = int((dictData["itemCount"] + pageSize - 1) / pageSize)

    # 遍历添加到字典项列表中
    for di in db_dictItem:
        dictData["list"].append(di.to_dict())

    return successResponseWrap(data=dictData)


# 获取指定字典项
@dictionary.get("/dict-item")
@jwt_required()
def getDictItem():
    dictTypeList = request.args.getlist("dictTypeList[]")
    dictType = request.args.get("dictType")

    filter_params = [Dict.deleted == 0, DictItem.deleted == 0]

    dictData = {}

    if dictTypeList:
        for dt in dictTypeList:
            db_dictItem = DictItem.query.join(Dict, DictItem.dict_id == Dict.id) \
                .filter(Dict.type == dt, *filter_params) \
                .all()
            dictData[dt] = [d.to_dict() for d in db_dictItem]
    elif dictType:
        db_dictItem = DictItem.query.join(Dict, DictItem.dict_id == Dict.id) \
            .filter(Dict.type == dictType, *filter_params) \
            .all()
        dictData[dictType] = [d.to_dict() for d in db_dictItem]
    else:
        db_dict = Dict.query.all()
        dictTypeList = [d.type for d in db_dict]

        for dt in dictTypeList:
            db_dictItem = DictItem.query.join(Dict, DictItem.dict_id == Dict.id) \
                .filter(Dict.type == dt, *filter_params) \
                .all()
            dictData[dt] = [d.to_dict() for d in db_dictItem]

    return successResponseWrap(data=dictData)


# 更新字典项
@dictionary.put("/dict-item/update")
@permission_required("dict-item:update")
def updateDictItem():
    dictItemId = request.json.get("id")
    label = request.json.get("label")
    value = request.json.get("value")
    sort = request.json.get("sort")
    isDefault = request.json.get("isDefault")
    deleted = request.json.get("deleted")
    description = request.json.get("description")
    updated_at = int(round(time.time() * 1000))

    result = DictItem.query.filter_by(id=dictItemId).update(
        {"label": label, "value": value, "sort": sort, "isDefault": isDefault, "deleted": deleted,
         "description": description, "updated_at": updated_at}
    )

    if not result:
        return failResponseWrap(5001, "字典项更新失败")

    db.session.commit()

    return successResponseWrap("字典项更新成功")


# 新增字典项
@dictionary.post("/dict-item/add")
@permission_required("dict-item:add")
def addDictItem():
    dictType = request.json.get("dictType")
    label = request.json.get("label")
    value = request.json.get("value")
    sort = request.json.get("sort")
    isDefault = request.json.get("isDefault")
    deleted = request.json.get("deleted")
    description = request.json.get("description")
    updated_at = int(round(time.time() * 1000))

    db_dict = Dict.query.filter_by(type=dictType).first()
    dictId = db_dict.id

    # 添加字典项
    dictItemInfo = DictItem(label=label, value=value, sort=sort, isDefault=isDefault, deleted=deleted,
                            description=description, updated_at=updated_at, dict_id=dictId)

    db.session.add(dictItemInfo)

    db.session.commit()

    return successResponseWrap("字典项添加成功")


# 删除字典项
@dictionary.delete("/dict-item/delete")
@permission_required("dict-item:delete")
def deleteDictItem():
    dictItemId = request.json.get("dictItemId")

    # 删除字典项
    DictItem.query.filter_by(id=dictItemId).delete()

    db.session.commit()

    return successResponseWrap("字典项删除成功")


# 性别
@dictionary.get("/dict/gender")
@jwt_required()
def getGender():
    data = [
        {"label": "女", "value": 0},
        {"label": "男", "value": 1},
    ]
    return successResponseWrap(data=data)


# 角色
@dictionary.get("/dict/role")
@jwt_required()
def getRole():
    db_roles = Role.query.all()

    roleDict = [{"label": r.nickname, "value": r.id} for r in db_roles]

    return successResponseWrap(data=roleDict)
