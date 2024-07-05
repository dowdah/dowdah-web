from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import config
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from celery import Celery
from flask_jwt_extended import JWTManager
import datetime


db = SQLAlchemy()
mail = Mail()
jwt = JWTManager()


def not_found_error(e):
    return {'success': False, 'code': 404, 'msg': 'Not found'}, 404


def method_not_allowed_error(e):
    return {'success': False, 'code': 405, 'msg': 'Method not allowed'}, 405


def make_celery(app=None):
    celery = Celery(
        app.import_name if app else 'celery_app',
        backend='redis://redis:6379/0',
        broker='redis://redis:6379/0'
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
