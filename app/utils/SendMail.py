# !/usr/bin/env python
# -*-coding: utf-8 -*-
"""
# @File    : SendMail.py
# @Time    : 2022/7/15 18:04
# @Author  : Shuai
# @Email   : ls12345666@qq.com
"""
from threading import Thread

from flask import current_app
from flask_mail import Message
from app import mail


# 异步邮件
def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


# 发送邮件(标题, 内容, [接收方])
def send_email(subject, text_body, recipients):
    app = current_app._get_current_object()
    msg = Message(subject, sender=app.config['MAIL_DEFAULT_SENDER'], recipients=recipients)
    msg.body = text_body
    thread = Thread(target=send_async_email, args=[app, msg])
    thread.start()
    return thread
