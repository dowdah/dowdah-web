from . import api_bp
from werkzeug.exceptions import HTTPException
import json


@api_bp.errorhandler(HTTPException)
def generic_error(e):
    response = e.get_response()
    response.data = json.dumps({
        "success": False,
        "code": e.code,
        "name": e.name,
        "msg": e.description,
    })
    response.content_type = "application/json"
    return response
