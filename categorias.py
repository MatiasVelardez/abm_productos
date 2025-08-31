from flask import Blueprint, request
from db import get_conn
from utils import ok, err, require_role
from flask_jwt_extended import jwt_required

categories_bp = Blueprint("categories", __name__, url_prefix="/categorias")

@categories_bp.get("")
@jwt_required()
def list_categorias():
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT id, nombre FROM categorias ORDER BY nombre ASC")
    rows = cur.fetchall(); cur.close(); conn.close()
    return ok(rows)

@categories_bp.post("")
@require_role("admin")
def create_categoria():
    b = request.get_json(silent=True) or {}
    nombre = (b.get("nombre") or "").strip()
    if not nombre: return err("nombre obligatorio", 400)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO categorias (nombre) VALUES (%s)", (nombre,))
    conn.commit()
    new_id = cur.lastrowid; cur.close(); conn.close()
    return ok({"id": new_id, "nombre": nombre}, 201)

@categories_bp.put("/<int:cid>")
@require_role("admin")
def update_categoria(cid):
    b = request.get_json(silent=True) or {}
    nombre = (b.get("nombre") or "").strip()
    if not nombre: return err("nombre obligatorio", 400)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE categorias SET nombre=%s WHERE id=%s", (nombre, cid))
    conn.commit(); cur.close(); conn.close()
    return ok({"id": cid, "nombre": nombre})

@categories_bp.delete("/<int:cid>")
@require_role("admin")
def delete_categoria(cid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM categorias WHERE id=%s", (cid,))
    conn.commit(); cur.close(); conn.close()
    return ok({"message":"Categoría eliminada"})
