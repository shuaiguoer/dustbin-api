from flask import Flask, request
from flask_cors import CORS
from flask_jwt_extended import get_jti
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy

from app.conf.StatusCode import TOKEN_IN_BLACKLIST
from app.conf.settings import Config
from app.utils.ConnectionRedis import redisConnection
from app.utils.JWTLoader import jwt
from app.utils.ResponseWrap import failResponseWrap

# 实例化SQLAlchemy
db = SQLAlchemy()  # 注意：实例化SQLAlchemy的代码必须要在引入蓝图之前

# 实例化Mail
mail = Mail()

# 导入蓝图
from app.views.user import user
from app.views.menu import menu
from app.views.role import role
from app.views.dictionary import dictionary
from app.views.qrcode import qrcode
from app.views.log import log
from app.views.monitor import monitor
from app.views.notice import notice


def create_app():
    app = Flask(__name__, static_folder='../static')

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

    # 在每次请求前运行
    @app.before_request
    def before_request():
        if request.method != "OPTIONS" and "login" not in request.path:
            # 获取jti
            token = request.headers.get("Authorization").split(" ")[1]
            jti = get_jti(token)

            # 效验access_token的jti是否在黑名单中
            rdb_blacklist = redisConnection(1)
            if rdb_blacklist.exists(jti):
                return failResponseWrap(*TOKEN_IN_BLACKLIST)

    # 注册蓝图
    app.register_blueprint(user)
    app.register_blueprint(menu)
    app.register_blueprint(role)
    app.register_blueprint(dictionary)
    app.register_blueprint(qrcode)
    app.register_blueprint(log)
    app.register_blueprint(monitor)
    app.register_blueprint(notice)

    return app
