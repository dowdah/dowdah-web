from flask import jsonify, request, g, abort, current_app, Blueprint
from ...models import User
from ... import db, redis_client
from ...decorators import turnstile_required, email_verification_required
import re
import random
import string


auth_bp = Blueprint('auth', __name__)
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
USERNAME_REGEX = re.compile(r'^(?=.{3,20}$)(?![_.])(?!.*[_.]{2})[a-zA-Z0-9._]+(?<![_.])$')
PASSWORD_REGEX = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?]).{8,}$")


@auth_bp.route('/register', methods=['POST'])
@turnstile_required(action='send_email_code_and_register')
@email_verification_required
def register():
    data = g.data
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    # 由于使用了 email_verification_required 装饰器，这里不需要再次验证 email 和 code
    if username is None or password is None:
        response_json = {
            'success': False,
            'code': 400,
            'msg': 'Missing required fields'
        }
        return jsonify(response_json), response_json['code']
    if not USERNAME_REGEX.match(username) or not PASSWORD_REGEX.match(password):
        response_json = {
            'success': False,
            'code': 400,
            'msg': 'Invalid username or password'
        }
        return jsonify(response_json), response_json['code']
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
@turnstile_required(action='login')
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


@auth_bp.route('/send-email-code', methods=['POST'])
@turnstile_required(action='send_email_code')
def send_email_code():
    email = g.data.get('email')
    if email and EMAIL_REGEX.match(email):
        if User.query.filter_by(email=email).first():
            response_json = {
                'success': False,
                'code': 400,
                'msg': 'Email address already in use'
            }
        else:
            code = ''.join(random.choices(string.digits, k=6))
            redis_client.set(f"email_verification_{email}", code,
                             ex=current_app.config['EMAIL_CODE_EXPIRATION'])
            task = current_app.celery.send_task('app.send_email', args=[[email],
                                                                        f"{code}为您的验证码",
                                                                        "email_verification.html"],
                                                kwargs={'code': code})
            response_json = {
                'success': True,
                'code': 202,
                'msg': 'Verification email task created',
                'task_id': task.id
            }
    else:
        response_json = {
            'success': False,
            'code': 400,
            'msg': 'Invalid email address'
        }
    return jsonify(response_json), response_json['code']


@auth_bp.route('/verify-email-code', methods=['POST'])
def verify_email_code():
    email = g.data.get('email')
    code = g.data.get('code')
    if email is None or code is None:
        response_json = {
            'success': False,
            'code': 400,
            'msg': 'Email or code not provided'
        }
    else:
        if EMAIL_REGEX.match(email):
            if redis_client.get(f"email_verification_{email}") == code:
                response_json = {
                    'success': True,
                    'code': 200,
                    'msg': 'Verification successful'
                }
            else:
                response_json = {
                    'success': False,
                    'code': 400,
                    'msg': 'Incorrect code'
                }
        else:
            response_json = {
                'success': False,
                'code': 400,
                'msg': 'Invalid email address'
            }
    return jsonify(response_json), response_json['code']


@auth_bp.route('/reset-password')
def send_reset_password_email():
    return abort(403)
    # username = request.args.get('username')
    # email = request.args.get('email')
    # user, user_1, user_2 = None, None, None
    # if username:
    #     user_1 = User.query.filter_by(username=username).first()
    # if email:
    #     user_2 = User.query.filter_by(email=email).first()
    # if user_1 and user_2:
    #     if user_1 != user_2:
    #         response_json = {
    #             'success': False,
    #             'code': 400,
    #             'msg': 'Attributes do not match'
    #         }
    #         return jsonify(response_json), response_json['code']
    #     else:
    #         user = user_1
    # elif user_1:
    #     user = user_1
    # elif user_2:
    #     user = user_2
    # else:
    #     response_json = {
    #         'success': False,
    #         'code': 400,
    #         'msg': 'User not found'
    #     }
    #     return jsonify(response_json), response_json['code']
    # task = current_app.celery.send_task('app.send_email', args=[[user.email],
    #                                                             "重置密码", "email_password_reset.html"],
    #                                     kwargs={'token': user.generate_email_token(), 'user': user.to_json()})
    # response_json = {
    #     'success': True,
    #     'code': 200,
    #     'msg': 'Reset password email sent',
    #     'task_id': task.id
    # }
    # return jsonify(response_json), response_json['code']


@auth_bp.route('/reset-password/<token>', methods=['POST'])
def reset_password(token):
    return abort(403)
    # username = g.data.get('username')
    # email = g.data.get('email')
    # password = g.data.get('password')
    # user, user_1, user_2 = None, None, None
    # if username:
    #     user_1 = User.query.filter_by(username=username).first()
    # if email:
    #     user_2 = User.query.filter_by(email=email).first()
    # if user_1 and user_2:
    #     if user_1 != user_2:
    #         response_json = {
    #             'success': False,
    #             'code': 400,
    #             'msg': 'Attributes do not match'
    #         }
    #         return jsonify(response_json), response_json['code']
    #     else:
    #         user = user_1
    # elif user_1:
    #     user = user_1
    # elif user_2:
    #     user = user_2
    # else:
    #     response_json = {
    #         'success': False,
    #         'code': 400,
    #         'msg': 'Account not found'
    #     }
    #     return jsonify(response_json), response_json['code']
    # if user.validate_email_token(token):
    #     user.password = password
    #     user.alternative_id = User.generate_alternative_id()
    #     db.session.add(user)
    #     db.session.commit()
    #     current_app.celery.send_task('app.send_email', args=[[user.email],
    #                                                          "密码重置成功", "email_password_reset.html"],
    #                                  kwargs={'user': user.to_json()})
    #     response_json = {
    #         'success': True,
    #         'code': 200,
    #         'msg': 'Successfully reset password',
    #         'user': user.to_json(),
    #         'access_token': user.generate_access_token(),
    #         'refresh_token': user.generate_refresh_token()
    #     }
    # else:
    #     response_json = {
    #         'success': False,
    #         'code': 400,
    #         'msg': 'Invalid token'
    #     }
    # return jsonify(response_json), response_json['code']
