from flask import Blueprint, request, g

v1_bp = Blueprint('v1', __name__)


from . import views
from .auth import auth_bp
from .webauthn import webauthn_bp
from .r2 import r2_bp
from .user import user_bp


v1_bp.register_blueprint(auth_bp, url_prefix='/auth')
v1_bp.register_blueprint(webauthn_bp, url_prefix='/webauthn')
v1_bp.register_blueprint(r2_bp, url_prefix='/r2')
v1_bp.register_blueprint(user_bp, url_prefix='/user')


@v1_bp.before_request
def before_request():
    # 将 application/json 与 multipart/form-data 的数据统一处理
    # g.temp = request.content_type
    methods_with_body = ['POST', 'PUT', 'PATCH']
    if request.method in methods_with_body:
        if request.content_type:
            if 'application/json' in request.content_type:
                g.data = request.get_json()
                g.files = None
            elif 'multipart/form-data' in request.content_type:
                g.data = request.form.to_dict()
                g.files = request.files
            else:
                g.data = None
                g.files = None
        else:
            g.data = None
            g.files = None
    else:
        g.data = None
        g.files = None
    if g.data:
        g.data = {k: v for k, v in g.data.items() if v is not None}
