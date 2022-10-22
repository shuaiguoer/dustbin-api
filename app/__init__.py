from flask import Flask, request
from flask_cors import CORS
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy

from app.conf.settings import Config
from app.modules.LogHandler import getLogHandler
from app.utils.JWTLoader import jwt

# 实例化SQLAlchemy
db = SQLAlchemy()  # 注意：实例化SQLAlchemy的代码必须要在引入蓝图之前

# 实例化Mail
mail = Mail()

# 导入蓝图
from app.Controller.userController import user
from app.Controller.menuController import menu
from app.Controller.roleController import role
from app.Controller.dictionaryController import dictionary
from app.Controller.qrcodeController import qrcode


def create_app():
    app = Flask(__name__, static_folder='../static')

    app.logger.addHandler(getLogHandler())

    # @app.before_request
    # def log_each_request():
    #     app.logger.info(
    #         '{} - {} - {}'.format(request.method, request.path, request.remote_addr))

    # 跨域
    CORS(app, supports_credentials=True)

    # 初始化Flask配置
    app.config.from_object(Config)

    # 初始化SQLAlchemy
    db.init_app(app)

    # 初始化JWT
    jwt.init_app(app)

    # 初始化Mail
    mail.init_app(app)

    # 注册蓝图
    app.register_blueprint(user)
    app.register_blueprint(menu)
    app.register_blueprint(role)
    app.register_blueprint(dictionary)
    app.register_blueprint(qrcode)

    return app
