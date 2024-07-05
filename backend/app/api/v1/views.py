from . import v1_bp
from flask import current_app, jsonify
from ...models import Permission


@v1_bp.route('/task/<task_id>')
def get_task(task_id):
    task = current_app.celery.AsyncResult(task_id)
    response_json = {'success': True, 'code': 200, 'task_status': task.status, 'task_result': task.result}
    return jsonify(response_json), response_json['code']


@v1_bp.route('/permissions')
def get_permission_info():
    response_json = {
        'success': True,
        'code': 200,
        'permissions': Permission.to_json()
    }
    return jsonify(response_json), response_json['code']
