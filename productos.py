from flask import Blueprint, request
from db import get_conn
from utils import ok, err, require_role
from flask_jwt_extended import jwt_required

products_bp = Blueprint("products", __name__, url_prefix="/productos")

# Helpers
def find_or_create_categoria(conn, nombre):
    if not nombre: return None
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT id FROM categorias WHERE nombre=%s", (nombre,))
    row = cur.fetchone()
    if row: 
        cur.close()
        return row["id"]
    cur2 = conn.cursor()
    cur2.execute("INSERT INTO categorias (nombre) VALUES (%s)", (nombre,))
    conn.commit()
    new_id = cur2.lastrowid
    cur2.close()
    cur.close()
    return new_id

# Listar (acceso para todos los logueados)
@products_bp.get("")
@jwt_required()
def list_productos():
    q = (request.args.get("q") or "").strip()
    page = int(request.args.get("page", 1))
    page_size = min(int(request.args.get("pageSize", 10)), 100)
    sort_by = (request.args.get("sortBy") or "created_at").lower()
    sort_dir = "asc" if (request.args.get("sortDir") or "desc").lower() == "asc" else "desc"
    marca_id = request.args.get("marcaId")
    categoria_id = request.args.get("categoriaId")

    allowed_sorts = {"nombre","precio","stock","created_at"}
    if sort_by not in allowed_sorts: sort_by = "created_at"
    where = []
    params = []
    if q:
        where.append("(p.nombre LIKE %s OR p.descripcion LIKE %s OR p.codigo_barra LIKE %s)")
        like = f"%{q}%"
        params += [like, like, like]
    if marca_id: where.append("p.marca_id=%s") or params.append(int(marca_id))
    if categoria_id: where.append("p.categoria_id=%s") or params.append(int(categoria_id))
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    offset = (page-1)*page_size

    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute(f"SELECT COUNT(*) total FROM productos p {where_sql}", params)
    total = cur.fetchone()["total"]; cur.close()

    cur = conn.cursor(dictionary=True)
    cur.execute(f"""
        SELECT p.id, p.nombre, p.descripcion, p.codigo_barra AS codigoBarra,
               p.precio, p.stock, p.marca_id AS marcaId, p.categoria_id AS categoriaId,
               p.created_at, p.updated_at
          FROM productos p
          {where_sql}
         ORDER BY {sort_by} {sort_dir}
         LIMIT %s OFFSET %s
    """, params + [page_size, offset])
    rows = cur.fetchall(); cur.close(); conn.close()
    return ok(rows, meta={"page":page,"pageSize":page_size,"total":total,"totalPages": (total+page_size-1)//page_size})

# Obtener uno (logueado)
@products_bp.get("/<int:pid>")
@jwt_required()
def get_producto(pid):
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT p.id, p.nombre, p.descripcion, p.codigo_barra AS codigoBarra,
               p.precio, p.stock, p.marca_id AS marcaId, p.categoria_id AS categoriaId,
               p.created_at, p.updated_at
          FROM productos p WHERE p.id=%s
    """, (pid,))
    row = cur.fetchone(); cur.close(); conn.close()
    if not row: return err("Producto no encontrado", 404)
    return ok(row)

# Crear (solo admin)
@products_bp.post("")
@require_role("admin")
def create_producto():
    b = request.get_json(silent=True) or {}
    nombre = (b.get("nombre") or "").strip()
    codigo_barra = (b.get("codigoBarra") or "").strip()
    precio = b.get("precio"); stock = b.get("stock")
    marca_id = b.get("marcaId"); categoria_id = b.get("categoriaId")
    categoria_nombre = (b.get("categoriaNombre") or "").strip()  # crear al vuelo

    errs=[]
    if not nombre: errs.append("El nombre es obligatorio.")
    if not codigo_barra: errs.append("El código de barra es obligatorio.")
    try:
        precio = float(precio);  assert precio >= 0
    except: errs.append("precio inválido")
    try:
        stock = int(stock);  assert stock >= 0
    except: errs.append("stock inválido")
    if errs: return err("; ".join(errs), 400)

    conn = get_conn()
    try:
        if categoria_nombre and not categoria_id:
            categoria_id = find_or_create_categoria(conn, categoria_nombre)

        cur = conn.cursor()
        cur.execute("""
            INSERT INTO productos (nombre, descripcion, codigo_barra, precio, stock, marca_id, categoria_id)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (nombre, b.get("descripcion"), codigo_barra, precio, stock, marca_id, categoria_id))
        conn.commit()
        new_id = cur.lastrowid; cur.close(); conn.close()
        return ok({"id":new_id, "nombre":nombre, "codigoBarra":codigo_barra,
                   "precio":precio, "stock":stock, "marcaId":marca_id, "categoriaId":categoria_id}, 201)
    except Exception as e:
        conn.rollback()
        conn.close()
        return err(str(e), 500)

# Actualizar (solo admin)
@products_bp.put("/<int:pid>")
@require_role("admin")
def update_producto(pid):
    b = request.get_json(silent=True) or {}
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM productos WHERE id=%s", (pid,))
    actual = cur.fetchone()
    if not actual:
        cur.close(); conn.close()
        return err("Producto no encontrado", 404)

    nombre = (b.get("nombre") or actual["nombre"]).strip()
    codigo_barra = (b.get("codigoBarra") or actual["codigo_barra"]).strip()
    descripcion = b.get("descripcion", actual.get("descripcion"))
    precio = b.get("precio", actual["precio"])
    stock = b.get("stock", actual["stock"])
    marca_id = b.get("marcaId", actual.get("marca_id"))
    categoria_id = b.get("categoriaId", actual.get("categoria_id"))
    categoria_nombre = (b.get("categoriaNombre") or "").strip()

    errs=[]
    if not nombre: errs.append("El nombre es obligatorio.")
    if not codigo_barra: errs.append("El código de barra es obligatorio.")
    try:
        precio = float(precio); assert precio >= 0
    except: errs.append("precio inválido")
    try:
        stock = int(stock); assert stock >= 0
    except: errs.append("stock inválido")
    if errs:
        cur.close(); conn.close()
        return err("; ".join(errs), 400)

    if categoria_nombre and not categoria_id:
        categoria_id = find_or_create_categoria(conn, categoria_nombre)

    upd = conn.cursor()
    upd.execute("""
        UPDATE productos
           SET nombre=%s, descripcion=%s, codigo_barra=%s,
               precio=%s, stock=%s, marca_id=%s, categoria_id=%s
         WHERE id=%s
    """, (nombre, descripcion, codigo_barra, precio, stock, marca_id, categoria_id, pid))
    conn.commit()
    upd.close(); cur.close(); conn.close()
    return ok({"id":pid,"nombre":nombre,"codigoBarra":codigo_barra,
               "precio":precio,"stock":stock,"marcaId":marca_id,"categoriaId":categoria_id})
    
# Borrar (solo admin)
@products_bp.delete("/<int:pid>")
@require_role("admin")
def delete_producto(pid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM productos WHERE id=%s", (pid,))
    if not cur.fetchone():
        cur.close(); conn.close()
        return err("Producto no encontrado", 404)
    cur.execute("DELETE FROM productos WHERE id=%s", (pid,))
    conn.commit(); cur.close(); conn.close()
    return ok({"message":"Producto eliminado"})
