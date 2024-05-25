from . import api_v1
from flask import jsonify
from ...models import User


@api_v1.route('/test', methods=['GET'])
def test():
    return {'status': 'success'}


@api_v1.route('/users')
def get_users():
    users = User.query.all()
    return jsonify([{'username': user.username, 'email': user.email} for user in users])
