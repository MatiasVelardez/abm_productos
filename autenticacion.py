from flask import Blueprint, request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from db import get_conn
from utils import ok, err, require_role

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

# Registrar usuario (solo admin)
@auth_bp.post("/register")
@require_role("admin")
def register():
    body = request.get_json(silent=True) or {}
    usuario = (body.get("usuario") or "").strip()
    password = body.get("password") or ""
    rol = body.get("rol", "empleado")
    if not usuario or not password:
        return err("usuario y password son obligatorios", 400)
    if rol not in ("admin", "empleado"):
        return err("rol inválido", 400)

    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT 1 FROM usuarios WHERE usuario=%s", (usuario,))
        if cur.fetchone():
            return err("Usuario ya existe", 409)
        ph = generate_password_hash(password)
        cur.execute("INSERT INTO usuarios (usuario, password_hash, rol) VALUES (%s,%s,%s)", (usuario, ph, rol))
        conn.commit()
        return ok({"usuario": usuario, "rol": rol}, code=201)
    finally:
        cur.close()
        conn.close()

# Login → devuelve JWT
@auth_bp.post("/login")
def login():
    body = request.get_json(silent=True) or {}
    usuario = (body.get("usuario") or "").strip()
    password = body.get("password") or ""
    if not usuario or not password:
        return err("usuario y password son obligatorios", 400)

    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT id, usuario, password_hash, rol FROM usuarios WHERE usuario=%s", (usuario,))
        row = cur.fetchone()
        if not row or not check_password_hash(row["password_hash"], password):
            return err("Credenciales inválidas", 401)
        # claims incluye rol para checks
        token = create_access_token(identity=str(row["id"]), additional_claims={"usuario": row["usuario"], "rol": row["rol"]})
        return ok({"token": token, "usuario": row["usuario"], "rol": row["rol"]})
    finally:
        cur.close()
        conn.close()

# Quién soy (debug)
@auth_bp.get("/me")
@jwt_required()
def me():
    from flask_jwt_extended import get_jwt
    return ok(get_jwt())
