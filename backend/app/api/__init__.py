from flask import Blueprint


api_bp = Blueprint('api', __name__)


from .v1 import v1_bp
from .test import test_bp
from . import errors


api_bp.register_blueprint(v1_bp, url_prefix='/v1')
api_bp.register_blueprint(test_bp, url_prefix='/test')
