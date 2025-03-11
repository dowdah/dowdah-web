from flask import jsonify, request, g, current_app, Blueprint
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes


import time
import base64


s3_bp = Blueprint('s3', __name__)
ALLOWED_AVATAR_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif']


@s3_bp.route('/get-avatar-upload-presigned-put', methods=['GET'])
def get_avatar_upload_presigned_put():
    avatar_proxy = current_app.config.get('AVATAR_PROXY')
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
            if file_extension == 'jpg':
                mime_type = 'image/jpeg'
            else:
                mime_type = f"image/{file_extension}"
            filename = f"avatar_{timestamp}.{file_extension}"
            presigned_url = user.generate_presigned_url_avatar(filename, mime_type)

            # 加密 presigned_url
            iv = get_random_bytes(12)  # 12字节 IV
            cipher = AES.new(current_app.config.get('SECRET_KEY').encode('utf-8'), AES.MODE_GCM, nonce=iv)
            ciphertext, tag = cipher.encrypt_and_digest(presigned_url.encode())
            encrypted_presigned_url = iv + ciphertext + tag

            response_json = {
                'success': True,
                'code': 200,
                'presigned': base64.b64encode(encrypted_presigned_url).decode('utf-8'),
                'avatar_url': user.avatar_url
            }

    return jsonify(response_json), response_json['code']
