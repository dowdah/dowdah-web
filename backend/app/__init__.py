from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import config
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
mail = Mail()


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    mail.init_app(app)
    db.init_app(app)
    from .api.v1 import api_v1 as api_blueprint_v1
    app.register_blueprint(api_blueprint_v1, url_prefix='/api/v1')

    @app.context_processor
    def inject_variables():
        return {'site_name': app.config['SITE_NAME']}

    return app
