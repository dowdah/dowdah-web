from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import config, Config
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from celery import Celery
from flask_jwt_extended import JWTManager
from botocore.client import Config as botoConfig
import datetime
import boto3
import redis
import os


db = SQLAlchemy()
mail = Mail()
jwt = JWTManager()
s3 = boto3.client('s3', aws_access_key_id=Config.R2_ACCESS_KEY, aws_secret_access_key=Config.R2_SECRET_KEY,
                    endpoint_url=Config.R2_ENDPOINT, config=botoConfig(signature_version='s3v4'))
REDIS_URL = os.environ.get('REDIS_URL', 'redis://redis:6379/0')
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)


def not_found_error(e):
    return {'success': False, 'code': 404, 'msg': 'Not found'}, 404


def method_not_allowed_error(e):
    return {'success': False, 'code': 405, 'msg': 'Method not allowed'}, 405


def make_celery(app=None):
    celery = Celery(
        app.import_name if app else 'celery_app',
        backend=REDIS_URL,
        broker=REDIS_URL
    )

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            if app:
                with app.app_context():
                    return self.run(*args, **kwargs)
            else:
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    if app:
        celery.conf.update(app.config)
    return celery


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    app.register_error_handler(404, not_found_error)
    app.register_error_handler(405, method_not_allowed_error)
    config[config_name].init_app(app)
    mail.init_app(app)
    db.init_app(app)
    jwt.init_app(app)
    celery = make_celery(app)
    app.celery = celery
    from .api import api_bp as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api')
    with app.app_context():
        # 导入模型，事件监听器和Celery任务
        from . import models
        from . import listeners
        from . import celery_tasks

    @app.context_processor
    def inject_variables():
        return {'site_name': app.config['SITE_NAME'], 'current_year': datetime.datetime.now().year,
                'domain': app.config['DOMAIN']}

    return app
