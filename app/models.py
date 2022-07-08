# !/usr/bin/env python3
# -*-coding: utf-8 -*-
"""
# @File    : models.py
# @Time    : 2022/7/8 23:30
# @Author  : Shuai
# @Email   : ls12345666@qq.com
"""
from app import db


class EntityBase(object):
    def to_json(self):
        fields = self.__dict__
        if "_sa_instance_state" in fields:
            del fields["_sa_instance_state"]

        return fields


class User(db.Model, EntityBase):
    __tablename__ = 'user'  # 数据库表名
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), index=True, nullable=False)
    age = db.Column(db.Integer)
    department = db.Column(db.String(20))


if __name__ == '__main__':
    from app import create_app

    app = create_app()

    with app.app_context():
        db.drop_all()
        db.create_all()
