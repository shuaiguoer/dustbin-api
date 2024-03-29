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
    def to_dict(self):
        fields = self.__dict__
        if "_sa_instance_state" in fields:
            del fields["_sa_instance_state"]

        return fields


class Dict(db.Model, EntityBase):
    __tablename__ = 'dict'

    id = db.Column(db.Integer, primary_key=True, info='字典表ID')
    name = db.Column(db.String(50), nullable=False, info='字典名称')
    type = db.Column(db.String(255), nullable=False, info='字典类型')
    description = db.Column(db.String(255), info='字典说明')
    deleted = db.Column(db.Integer, nullable=False, server_default=db.FetchedValue(), info='字典是否禁用')


class DictItem(db.Model, EntityBase):
    __tablename__ = 'dictItem'

    id = db.Column(db.Integer, primary_key=True, info='字典项ID')
    label = db.Column(db.String(20), nullable=False, info='字典项名称')
    value = db.Column(db.String(50), nullable=False, info='字典项值')
    sort = db.Column(db.Integer, nullable=False, server_default=db.FetchedValue(), info='字典项顺序(越小越靠前)')
    isDefault = db.Column(db.Integer, nullable=False, server_default=db.FetchedValue(),
                          info='是否默认(1:默认, 0:非默认)')
    description = db.Column(db.String(255), info='字典项说明')
    deleted = db.Column(db.Integer, nullable=False, server_default=db.FetchedValue(), info='字典项是否禁用')
    updated_at = db.Column(db.String(20), nullable=False, info='更新时间')
    dict_id = db.Column(db.Integer, nullable=False, info='字典ID')


class Menu(db.Model, EntityBase):
    __tablename__ = 'menu'

    id = db.Column(db.Integer, primary_key=True, info='菜单主键')
    name = db.Column(db.String(50), nullable=False, info='菜单名称')
    path = db.Column(db.String(50), nullable=False, info='菜单路径')
    component = db.Column(db.String(50), nullable=False, info='菜单组件名称')
    redirect = db.Column(db.String(255), info='菜单跳转链接')
    title = db.Column(db.String(50), info='菜单标题')
    icon = db.Column(db.String(50), info='菜单图标名称')
    hidden = db.Column(db.Integer, nullable=False, server_default=db.FetchedValue(), info='菜单: 显示(0) | 隐藏(1)')
    disabled = db.Column(db.Integer, nullable=False, server_default=db.FetchedValue(), info='停用: 正常(0) | 停用(1)')
    sort = db.Column(db.Integer, nullable=False, server_default=db.FetchedValue(), info='排序(越小越靠前)')
    type = db.Column(db.Integer, nullable=False, server_default=db.FetchedValue(), info='类型: 目录(0) 菜单(1) 权限(2)')
    pid = db.Column(db.Integer, nullable=False, server_default=db.FetchedValue(), info='父菜单ID')


class Qrcode(db.Model, EntityBase):
    __tablename__ = 'qrcode'

    id = db.Column(db.Integer, primary_key=True, info='ID')
    source = db.Column(db.String(255), nullable=False, info='源代码')
    target = db.Column(db.String(255), nullable=False, info='目标地址')
    description = db.Column(db.String(255), info='描述信息')
    updated_at = db.Column(db.String(20), nullable=False, info='更新时间')
    deleted = db.Column(db.Integer, nullable=False, server_default=db.FetchedValue(), info='是否删除')


class Role(db.Model, EntityBase):
    __tablename__ = 'role'

    id = db.Column(db.Integer, primary_key=True, info='角色主键')
    name = db.Column(db.String(50), nullable=False, info='角色名称')
    nickname = db.Column(db.String(50), nullable=False, info='中文名称')
    description = db.Column(db.String(255), info='角色描述')
    sort = db.Column(db.Integer, nullable=False, server_default=db.FetchedValue(), info='显示顺序(越小越靠前)')


class RoleMenu(db.Model, EntityBase):
    __tablename__ = 'role_menu'

    id = db.Column(db.Integer, primary_key=True, info='角色菜单表主键')
    role_id = db.Column(db.ForeignKey('role.id'), nullable=False, index=True, info='角色ID')
    menu_id = db.Column(db.ForeignKey('menu.id'), nullable=False, index=True, info='菜单ID')
    deleted = db.Column(db.Integer, nullable=False, server_default=db.FetchedValue(),
                        info='是否删除: 删除(1) 未删除(0)')

    menu = db.relationship('Menu', primaryjoin='RoleMenu.menu_id == Menu.id', backref='role_menus')
    role = db.relationship('Role', primaryjoin='RoleMenu.role_id == Role.id', backref='role_menus')


class User(db.Model, EntityBase):
    __tablename__ = 'user'

    userId = db.Column(db.Integer, primary_key=True, info='用户主键')
    username = db.Column(db.String(50), nullable=False, info='用户名称')
    password = db.Column(db.String(50), server_default=db.FetchedValue(), nullable=False, info='用户密码')
    email = db.Column(db.String(50), info='用户邮箱')
    avatar = db.Column(db.String(255), info='用户头像地址')
    gender = db.Column(db.Integer, server_default=db.FetchedValue(), info='用户性别')
    introduction = db.Column(db.String(255), info='用户介绍')
    registration_time = db.Column(db.String(50), nullable=False, info='用户注册时间')


class UserRole(db.Model, EntityBase):
    __tablename__ = 'user_role'

    id = db.Column(db.Integer, primary_key=True, info='用户角色映射表主键')
    user_id = db.Column(db.ForeignKey('user.userId'), nullable=False, index=True, info='用户ID')
    role_id = db.Column(db.ForeignKey('role.id'), nullable=False, index=True, info='角色ID')

    role = db.relationship('Role', primaryjoin='UserRole.role_id == Role.id', backref='user_roles')
    user = db.relationship('User', primaryjoin='UserRole.user_id == User.userId', backref='user_roles')


class Notice(db.Model):
    __tablename__ = 'notice'

    id = db.Column(db.Integer, primary_key=True, info='消息主键')
    title = db.Column(db.String(255), nullable=False, info='消息标题')
    content = db.Column(db.Text, nullable=False, info='消息内容')
    status = db.Column(db.Integer, nullable=False, server_default=db.FetchedValue(),
                       info='消息状态: 已发: (1), 草稿: (2)')
    sender_id = db.Column(db.Integer, nullable=False, info='发送者ID')
    created_at = db.Column(db.String(20), nullable=False, info='创建时间')


class NoticeUser(db.Model):
    __tablename__ = 'notice_user'

    id = db.Column(db.Integer, primary_key=True, info='用户消息主键')
    notice_id = db.Column(db.ForeignKey('notice.id'), nullable=False, index=True, info='消息ID')
    recipient_id = db.Column(db.ForeignKey('user.userId'), nullable=False, index=True, info='接收者ID')
    state = db.Column(db.Integer, nullable=False, server_default=db.FetchedValue(), info='状态: 已读(1) | 未读(0)')
    created_at = db.Column(db.String(20), nullable=False, info='拉取消息时间')
    deleted = db.Column(db.Integer, nullable=False, server_default=db.FetchedValue(),
                        info='是否删除: 已删(1) | 未删(0)')
    read_time = db.Column(db.String(20), info='读取时间')

    notice = db.relationship('Notice', primaryjoin='NoticeUser.notice_id == Notice.id', backref='notice_users')
    recipient = db.relationship('User', primaryjoin='NoticeUser.recipient_id == User.userId', backref='notice_users')


class OperationLog(db.Model):
    __tablename__ = 'operationLog'

    id = db.Column(db.Integer, primary_key=True, info='操作日志主键ID')
    username = db.Column(db.String(50), nullable=False, info='操作人员')
    systemModule = db.Column(db.String(50), nullable=False, info='系统模块')
    operationType = db.Column(db.Integer, nullable=False, info='操作类型')
    requestMethod = db.Column(db.String(10), nullable=False, info='请求方式')
    ipaddr = db.Column(db.String(50), nullable=False, info='IP地址')
    location = db.Column(db.String(255), nullable=False, info='操作地点')
    status = db.Column(db.Integer, nullable=False, server_default=db.FetchedValue(), info='操作状态')
    requestPath = db.Column(db.String(255), nullable=False, info='请求地址')
    requestParam = db.Column(db.Text, info='请求参数')
    returnParam = db.Column(db.Text, nullable=False, info='返回参数')
    operation_time = db.Column(db.String(20), nullable=False, info='操作时间')


class LoginLog(db.Model):
    __tablename__ = 'loginLog'

    id = db.Column(db.Integer, primary_key=True, info='登录日志主键ID')
    username = db.Column(db.String(50), nullable=False, info='用户名称')
    ipaddr = db.Column(db.String(50), nullable=False, info='IP地址')
    location = db.Column(db.String(255), nullable=False, info='登录地点')
    browser = db.Column(db.String(50), nullable=False, info='浏览器')
    os = db.Column(db.String(50), nullable=False, info='操作系统')
    device = db.Column(db.String(50), nullable=False, info='设备')
    status = db.Column(db.Integer, nullable=False, server_default=db.FetchedValue(), info='登录状态')
    msg = db.Column(db.String(50), nullable=False, info='操作信息')
    login_time = db.Column(db.String(50), nullable=False, info='登录时间')


class Action(db.Model):
    __tablename__ = 'action'

    id = db.Column(db.Integer, primary_key=True, info='动作主键ID')
    userId = db.Column(db.Integer, nullable=False, info='用户ID')
    module = db.Column(db.String(50), nullable=False, info='模块')
    bizNo = db.Column(db.String(50), info='业务编号')
    operation = db.Column(db.String(50), nullable=False, info='操作')
    detail = db.Column(db.String(255), info='详情')
    created_at = db.Column(db.String(20), nullable=False, info='创建时间')


if __name__ == '__main__':
    from app import create_app

    app = create_app()

    with app.app_context():
        db.drop_all()
        db.create_all()
