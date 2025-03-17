from flask import jsonify, request, g, current_app, Blueprint
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from ... import db


import time
import base64
import mimetypes
import json


r2_bp = Blueprint('r2', __name__)
ALLOWED_AVATAR_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif']
MAX_AVATAR_SIZE = 5 * 1024 * 1024  # 5MB


def generate_params(key, method, verbose_feedback=False, **additional_params):
    expires_timestamp = int(time.time()) + current_app.config['R2_PARAM_EXPIRATION']
    mime_type, _ = mimetypes.guess_type(key.split('/')[-1])
    params = {
        'expires': expires_timestamp,
        'key': key,
        'mime_type': mime_type,
        'method': method,
        'verbose_feedback': verbose_feedback
    }
    params.update(additional_params)
    iv = get_random_bytes(12)
    cipher = AES.new(current_app.config['SECRET_KEY'].encode('utf-8'), AES.MODE_GCM, nonce=iv)
    ciphertext, tag = cipher.encrypt_and_digest(json.dumps(params).encode('utf-8'))
    encrypted_params = iv + ciphertext + tag
    return base64.b64encode(encrypted_params).decode('utf-8')


def decrypt_str(encrypted_str):
    encrypted_str = base64.b64decode(encrypted_str)
    iv = encrypted_str[:12]
    ciphertext = encrypted_str[12:-16]
    tag = encrypted_str[-16:]
    cipher = AES.new(current_app.config['SECRET_KEY'].encode('utf-8'), AES.MODE_GCM, nonce=iv)
    decrypted_str = cipher.decrypt_and_verify(ciphertext, tag)
    return decrypted_str.decode('utf-8')


@r2_bp.route('/upload-avatar', methods=['GET'])
def upload_avatar():
    r2_proxy = current_app.config.get('R2_PROXY')
    user = g.current_user
    timestamp = int(time.time())
    file_extension = request.args.get('ext')
    if file_extension is None:
        response_json = {
            'success': False,
            'code': 400,
            'msg': 'Missing file extension.'
        }
    else:
        file_extension = file_extension.lower()
        if file_extension not in ALLOWED_AVATAR_EXTENSIONS:
            response_json = {
                'success': False,
                'code': 400,
                'msg': 'Invalid file extension. Valid extensions: jpg, jpeg, png, gif.'
            }
        else:
            key = f"{user.r2_uuid}/avatar_{timestamp}.{file_extension}"
            if user.avatar_filename is not None:
                r2_params = generate_params(key, 'avatar',
                                            previous_avatar_key=f"{user.r2_uuid}/{user.avatar_filename}",
                                            max_size=MAX_AVATAR_SIZE)
            else:
                r2_params = generate_params(key, 'avatar', max_size=MAX_AVATAR_SIZE)
            response_json = {
                'success': True,
                'code': 200,
                'r2_params': r2_params,
                'r2_proxy': r2_proxy,
                'new_avatar_url': f"{current_app.config['R2_PUBLIC_URL']}/{key}"
            }
    return jsonify(response_json), response_json['code']


@r2_bp.route('/confirm-new-avatar', methods=['POST'])
def confirm_new_avatar():
    user = g.current_user
    new_avatar_key = g.data.get('key')
    if new_avatar_key is None:
        response_json = {
            'success': False,
            'code': 400,
            'msg': 'Missing key'
        }
    else:
        try:
            new_avatar_key = decrypt_str(new_avatar_key)
            uuid, filename = new_avatar_key.split('/')
        except:
            response_json = {
                'success': False,
                'code': 400,
                'msg': 'Invalid key'
            }
        else:
            if uuid != user.r2_uuid:
                response_json = {
                    'success': False,
                    'code': 400,
                    'msg': 'UUID does not match'
                }
            else:
                user.avatar_filename = filename
                db.session.commit()
                response_json = {
                    'success': True,
                    'code': 200,
                    'msg': 'Avatar updated successfully'
                }
    return jsonify(response_json), response_json['code']
