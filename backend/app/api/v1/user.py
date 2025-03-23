from flask import jsonify, request, g, abort, current_app, Blueprint
from ...models import User
import re


user_bp = Blueprint('user', __name__)
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


@user_bp.route('/exists', methods=['POST'])
def exists():
    email = g.data.get('email')
    username = g.data.get('username')
    if email and username:
        response_json = {
            'success': False,
            'code': 400,
            'msg': 'Both email and username provided'
        }
    elif email:
        if EMAIL_REGEX.match(email):
            if User.query.filter_by(email=email).first():
                response_json = {
                    'success': True,
                    'code': 200,
                    'exists': True
                }
            else:
                response_json = {
                    'success': True,
                    'code': 200,
                    'exists': False
                }
        else:
            response_json = {
                'success': False,
                'code': 400,
                'msg': 'Invalid email address'
            }
    elif username:
        if User.query.filter_by(username=username).first():
            response_json = {
                'success': True,
                'code': 200,
                'exists': True
            }
        else:
            response_json = {
                'success': True,
                'code': 200,
                'exists': False
            }
    else:
        response_json = {
            'success': False,
            'code': 400,
            'msg': 'Neither email nor username provided'
        }
    return jsonify(response_json), response_json['code']
