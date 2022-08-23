from flask import Flask
from flask_cors import CORS
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy

from app.conf.settings import Config
from app.utils.JWTLoader import jwt

# 实例化SQLAlchemy
db = SQLAlchemy()  # 注意：实例化SQLAlchemy的代码必须要在引入蓝图之前

# 实例化Mail
mail = Mail()

# 导入蓝图
from app.views.user import user
from app.views.menu import menu
from app.views.role import role
from app.views.dict import dictionary


def create_app():
    app = Flask(__name__)

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

    return app
