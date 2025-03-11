from flask import jsonify, request, g, current_app, Blueprint


import urllib.parse


s3_bp = Blueprint('s3', __name__)
ALLOWED_AVATAR_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif']


@s3_bp.route('/get-avatar-upload-presigned-put', methods=['GET'])
def get_avatar_upload_presigned_put():
    avatar_proxy = current_app.config.get('AVATAR_PROXY')
    user = g.current_user
    file_extension = request.args.get('ext')
    if file_extension is None:
        response_json = {
            'success': False,
            'code': 400,
            'msg': 'Missing file_extension.'
        }
    else:
        file_extension = file_extension.lower()
        if file_extension not in ALLOWED_AVATAR_EXTENSIONS:
            response_json = {
                'success': False,
                'code': 400,
                'msg': 'Invalid file_extension.'
            }
        else:
            mime_type = f"image/{file_extension}"
            presigned_url = (f"{avatar_proxy}?presigned-url="
                             f"{urllib.parse.quote(user.generate_presigned_url_avatar(file_extension, mime_type))}")
            response_json = {
                'success': True,
                'code': 200,
                'presigned_url': presigned_url,
                'avatar_url': user.avatar_url
            }
    return jsonify(response_json), response_json['code']
