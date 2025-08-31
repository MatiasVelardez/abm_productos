from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from functools import wraps

def ok(data=None, meta=None, code=200):
    payload = {"status": "success"}
    if meta is not None: payload["meta"] = meta
    if data is not None: payload["data"] = data
    return jsonify(payload), code

def err(message, code=400):
    return jsonify({"status": "error", "message": message}), code

def require_role(*roles):
    """Proteger rutas por rol (ej: @require_role('admin'))"""
    def wrapper(fn):
        @wraps(fn)
        def decorated(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            rol = claims.get("rol")
            if rol not in roles:
                return err("No autorizado", 403)
            return fn(*args, **kwargs)
        return decorated
    return wrapper
