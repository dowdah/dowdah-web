from flask import jsonify, request, g, abort, current_app, Blueprint
from ...models import User
from ... import db


auth_bp = Blueprint('auth', __name__)


# 用户注册路由
@auth_bp.route('/register', methods=['POST'])
def register():
    data = g.data
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
        response_json = {
            'success': False,
            'code': 400,
            'msg': 'User already exists'
        }
    else:
        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        response_json = {
            'success': True,
            'code': 201,
            'msg': 'User created successfully',
            'access_token': new_user.generate_access_token(),
            'refresh_token': new_user.generate_refresh_token(),
            'user': new_user.to_json()
        }
    return response_json, response_json['code']


# 用户登录路由
@auth_bp.route('/login', methods=['POST'])
def login():
    data = g.data
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    user = None
    if username is None and email is None:
        response_json = {
            'success': False,
            'code': 400,
            'msg': 'No username or email provided'
        }
    elif username is not None and email is not None:
        response_json = {
            'success': False,
            'code': 400,
            'msg': 'Both username and email provided'
        }
    else:
        if username is not None:
            user = User.query.filter_by(username=username).first()
        elif email is not None:
            user = User.query.filter_by(email=email).first()
        if user is not None and user.verify_password(password):
            response_json = {
                'success': True,
                'code': 200,
                'msg': 'Login successful',
                'access_token': user.generate_access_token(),
                'refresh_token': user.generate_refresh_token(),
                'user': user.to_json()
            }
        else:
            response_json = {
                'success': False,
                'code': 401,
                'msg': 'Incorrect credentials'
            }
    return jsonify(response_json), response_json['code']


@auth_bp.route('/me', methods=['GET'])
def get_me():
    user = g.current_user
    response_json = {
        'success': True,
        'code': 200,
        'user': user.to_json(),
        'token_type': g.token_type
    }
    return jsonify(response_json), response_json['code']


@auth_bp.route('/refresh', methods=['GET'])
def refresh_access_token():
    user = g.current_user
    response_json = {
        'success': True,
        'code': 200,
        'access_token': user.generate_access_token()
    }
    return jsonify(response_json), response_json['code']
