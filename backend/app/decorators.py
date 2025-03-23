from functools import wraps
from flask import abort, g, current_app, jsonify
from .models import Permission
from .security import verify_turnstile, verify_email_code


def permission_required(perm):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not g.current_user.can(perm):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_only(f):
    return permission_required(Permission.ADMIN)(f)


def turnstile_required(action=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            production_mode = not (current_app.config.get('DEBUG') or current_app.config.get('TESTING'))
            if production_mode or not g.data.get('postman'):
                encrypted_turnstile_response = g.data.get('turnstile')
                fingerprint = g.data.get('fingerprint')
                if encrypted_turnstile_response is None or fingerprint is None:
                    response_json = {
                        'success': False,
                        'code': 400,
                        'msg': 'Missing turnstile response or fingerprint'
                    }
                    return jsonify(response_json), response_json['code']
                else:
                    turnstile_verify_response = verify_turnstile(encrypted_turnstile_response, fingerprint, action)
                    if not turnstile_verify_response['success']:
                        return jsonify(turnstile_verify_response), turnstile_verify_response['code']
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def email_verification_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        email = g.data.get('email')
        code = g.data.get('code')
        if email is None or code is None:
            response_json = {
                'success': False,
                'code': 400,
                'msg': 'Missing email or code'
            }
            return jsonify(response_json), response_json['code']
        else:
            email_verify_response = verify_email_code(email, code)
            if not email_verify_response['success']:
                return jsonify(email_verify_response), email_verify_response['code']
        return f(*args, **kwargs)
    return decorated_function
