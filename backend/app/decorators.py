from functools import wraps
from flask import abort, g
from .models import Permission


def permission_required(perm):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not g.current_user.can(perm):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_only(f):
    return permission_required(Permission.ADMIN)(f)
