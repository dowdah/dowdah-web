from flask import jsonify, request, g, abort, current_app, Blueprint
from datetime import datetime, timezone
from ...models import User
from ... import db, redis_client
from ...crypto import decrypt_json


auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    return abort(403)
    # data = g.data
    # username = data.get('username')
    # email = data.get('email')
    # password = data.get('password')
    # if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
    #     response_json = {
    #         'success': False,
    #         'code': 400,
    #         'msg': 'User already exists'
    #     }
    # else:
    #     new_user = User(username=username, email=email, password=password)
    #     db.session.add(new_user)
    #     db.session.commit()
    #     response_json = {
    #         'success': True,
    #         'code': 201,
    #         'msg': 'User created successfully',
    #         'access_token': new_user.generate_access_token(),
    #         'refresh_token': new_user.generate_refresh_token(),
    #         'user': new_user.to_json()
    #     }
    # return response_json, response_json['code']


# 用户登录路由
@auth_bp.route('/login', methods=['POST'])
def login():
    data = g.data
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    encrypted_turnstile_response = data.get('turnstile')
    fingerprint = data.get('fingerprint')
    user = None
    non_production = current_app.config.get('DEBUG') or current_app.config.get('TESTING')
    if encrypted_turnstile_response is None or fingerprint is None:
        if not non_production:
            response_json = {
                'success': False,
                'code': 400,
                'msg': 'Missing turnstile response or fingerprint'
            }
            return jsonify(response_json), response_json['code']
    else:
        try:
            turnstile_response = decrypt_json(current_app.config['SECRET_KEY'], encrypted_turnstile_response)
        except:
            response_json = {
                'success': False,
                'code': 400,
                'msg': 'Invalid turnstile response'
            }
            return jsonify(response_json), response_json['code']
        if turnstile_response['cdata'] != fingerprint or turnstile_response['action'] != 'login':
            response_json = {
                'success': False,
                'code': 400,
                'msg': 'Invalid turnstile response'
            }
            return jsonify(response_json), response_json['code']
        if redis_client.get(encrypted_turnstile_response):
            response_json = {
                'success': False,
                'code': 400,
                'msg': 'Used turnstile'
            }
            return jsonify(response_json), response_json['code']
        challenge_time = datetime.strptime(turnstile_response['challenge_ts'],
                                           "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
        time_diff = (datetime.now(timezone.utc) - challenge_time).total_seconds()
        if time_diff > current_app.config['TURNSTILE_EXPIRATION']:
            response_json = {
                'success': False,
                'code': 400,
                'msg': 'Turnstile response expired'
            }
            return jsonify(response_json), response_json['code']
        redis_client.set(encrypted_turnstile_response, 'used', ex=current_app.config['TURNSTILE_EXPIRATION'])
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


@auth_bp.route('/send-verification', methods=['GET'])
def send_verification():
    return abort(403)
    # if g.current_user.confirmed:
    #     response_json = {
    #         'success': False,
    #         'code': 400,
    #         'msg': 'Email address already verified'
    #     }
    # else:
    #     task = current_app.celery.send_task('app.send_email', args=[[g.current_user.email],
    #                                                                 "请验证你的邮箱", "email_confirm.html"],
    #                                         kwargs={'token': g.current_user.generate_email_token(), 'user': g.current_user.to_json()})
    #     response_json = {
    #         'success': True,
    #         'code': 200,
    #         'msg': 'Verification email sent',
    #         'task_id': task.id
    #     }
    # return jsonify(response_json), response_json['code']


@auth_bp.route('/verify-email/<token>')
def verify_email(token):
    return abort(403)
    # if g.current_user.confirmed:
    #     response_json = {
    #         'success': False,
    #         'code': 400,
    #         'msg': 'Email address already verified'
    #     }
    # elif g.current_user.validate_email_token(token):
    #     g.current_user.confirmed = True
    #     db.session.add(g.current_user)
    #     db.session.commit()
    #     response_json = {
    #         'success': True,
    #         'code': 200,
    #         'msg': 'Successfully verified email address'
    #     }
    # else:
    #     response_json = {
    #         'success': False,
    #         'code': 400,
    #         'msg': 'Invalid token'
    #     }
    # return jsonify(response_json), response_json['code']


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
