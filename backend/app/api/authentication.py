from flask import g, abort, request, jsonify, current_app
from ..models import User, Permission
from . import api_bp
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError


BYPASS_AUTH = ['api.v1.auth.login', 'api.v1.auth.register', 'api.v1.webauthn.webauthn_login_begin',
               'api.v1.webauthn.webauthn_login_complete']
CONFIRMATION_BYPASS = BYPASS_AUTH + ['api.v1.auth.send_confirmation', 'api.v1.auth.confirm', 'api.v1.auth.get_me']


@api_bp.before_request
def before_request():
    g.current_user = None
    g.token_type = None
    g.is_anonymous = True
    if 'Authorization' in request.headers:
        try:
            token = request.headers['Authorization'].split()[1]
            claims = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
            token_type = claims.get('type')
            user = User.query.filter_by(alternative_id=claims['sub']).first()
            if user is not None and user.can(Permission.LOGIN):
                user.ping()
                g.current_user = user
                g.is_anonymous = False
                g.token_type = token_type
        except (IndexError, ExpiredSignatureError, InvalidTokenError) as e:
            if str(e) == 'Signature has expired':
                response_json = {
                    'success': False,
                    'code': 401,
                    'msg': 'Token has expired. Please refresh current page.'
                }
                return jsonify(response_json), 401
    if request.endpoint not in BYPASS_AUTH:
        if g.is_anonymous:
            abort(401)
    if not (request.endpoint in CONFIRMATION_BYPASS or g.is_anonymous or g.current_user.confirmed):
        # User is not confirmed
        response_json = {
            'success': False,
            'code': 403,
            'msg': 'User is not confirmed.'
        }
        return jsonify(response_json), 403