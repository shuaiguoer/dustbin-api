# !/usr/bin/env python3
# -*-coding: utf-8 -*-
"""
# @File    : manage.py
# @Time    : 2022/7/8 22:34
# @Author  : Shuai
# @Email   : ls12345666@qq.com
"""
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from app import create_app, db

app = create_app()
manager = Manager(app)

Migrate(app, db)
manager.add_command("db", MigrateCommand)

if __name__ == '__main__':
    manager.run()
