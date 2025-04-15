from flask import g, abort, request, jsonify, current_app
from ..models import User, Permission
from . import api_bp
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError


BYPASS_AUTH = ['api.v1.auth.login', 'api.v1.auth.register', 'api.v1.webauthn.webauthn_login_begin',
               'api.v1.webauthn.webauthn_login_complete', 'api.v1.auth.send_email_code',
               'api.v1.auth.verify_email_code', 'api.v1.get_task', 'api.v1.user.exists', 'api.v1.wx.view',
               'api.v1.wx.check_bind_request']
ALLOW_REFRESH_TOKEN = ['api.v1.auth.refresh_access_token']
WECHAT_BOUND_BYPASS = (BYPASS_AUTH + ALLOW_REFRESH_TOKEN +
                       ['api.v1.auth.bind_wechat', 'api.v1.auth.get_me', 'api.v1.get_permission_info'])


@api_bp.before_request
def before_request():
    g.current_user = None
    g.token_type = None
    g.is_anonymous = True

    # 如果不需要认证的请求直接跳过
    if request.endpoint in BYPASS_AUTH:
        return

    # 提取 token 和用户信息
    auth_header = request.headers.get('Authorization')
    if auth_header:
        try:
            token = auth_header.split()[1]
            claims = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
            token_type = claims.get('type')
            user = User.query.filter_by(alternative_id=claims['sub']).first()

            if user:
                user.ping()
                g.current_user = user
                g.is_anonymous = False
                g.token_type = token_type
        except (IndexError, ExpiredSignatureError, InvalidTokenError) as e:
            if str(e) == 'Signature has expired':
                return jsonify({
                    'success': False,
                    'code': 401,
                    'msg': 'Token has expired'
                }), 401
            else:
                return jsonify({
                    'success': False,
                    'code': 401,
                    'msg': 'Invalid token'
                }), 401

    # 如果是匿名且需要认证的 endpoint，返回 401
    if g.is_anonymous:
        return jsonify({
            'success': False,
            'code': 401,
            'msg': 'Authentication required'
        }), 401

    # 检查用户是否绑定 WeChat
    if request.endpoint not in WECHAT_BOUND_BYPASS and not g.current_user.wechat_bound:
        return jsonify({
            'success': False,
            'code': 403,
            'msg': 'User is not WeChat bound'
        }), 403

    # 检查是否允许使用 refresh token
    if g.token_type == 'refresh' and request.endpoint not in ALLOW_REFRESH_TOKEN:
        return jsonify({
            'success': False,
            'code': 403,
            'msg': 'Refresh token is not allowed for this endpoint'
        }), 403
