from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from app.conf.settings import Config

# 实例化SQLAlchemy
db = SQLAlchemy()  # 注意：实例化SQLAlchemy的代码必须要在引入蓝图之前

# 导入蓝图
from app.views.user import user


def create_app():
    app = Flask(__name__)

    # 初始化Flask配置
    app.config.from_object(Config)

    # 初始化SQLAlchemy
    db.init_app(app)

    # 注册蓝图
    app.register_blueprint(user)

    return app
