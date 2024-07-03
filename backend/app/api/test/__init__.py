from flask import Blueprint, abort, current_app, jsonify

test_bp = Blueprint('test', __name__)


@test_bp.route('/process/<name>')
def process(name):
    new_task = current_app.celery.send_task('app.reverse', args=[name])
    response_json = {'success': True, 'code': 200, 'task_id': new_task.id}
    return jsonify(response_json), response_json['code']


@test_bp.route('/task/<task_id>')
def get_task(task_id):
    task = current_app.celery.AsyncResult(task_id)
    response_json = {'success': True, 'code': 200, 'task_status': task.status, 'task_result': task.result}
    return jsonify(response_json), response_json['code']
