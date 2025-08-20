from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector

# Crear la aplicación Flask
app = Flask(__name__)
CORS(app)  # Permite que React pueda conectarse

# Configuración de conexión
db_config = {
    'host': 'localhost',
    'user': 'root',        # Cambiá si tu MySQL tiene otro usuario
    'password': '',        # Poné tu contraseña de MySQL si tiene
    'database': 'abm_productos'  # Base de datos que creaste
}

# ---------- RUTAS BÁSICAS ----------
@app.route("/")
def home():
    return "¡Hola, backend funcionando!"

# ---------- LISTAR PRODUCTOS con búsqueda, filtros, orden y paginación ----------
@app.get("/productos")
def get_productos():
    # Params
    q = (request.args.get("q") or "").strip()
    page = request.args.get("page", "1")
    page_size = request.args.get("pageSize", "10")
    sort_by = (request.args.get("sortBy") or "created_at").strip().lower()
    sort_dir = (request.args.get("sortDir") or "desc").strip().lower()
    marca_id = request.args.get("marcaId")
    categoria_id = request.args.get("categoriaId")

    # Helpers
    def to_int(val, default):
        try:
            v = int(val)
            return v if v > 0 else default
        except (TypeError, ValueError):
            return default

    page = to_int(page, 1)
    page_size = to_int(page_size, 10)
    if page_size > 100:
        page_size = 100

    allowed_sorts = {"nombre", "precio", "stock", "created_at"}
    if sort_by not in allowed_sorts:
        sort_by = "created_at"
    sort_dir = "asc" if sort_dir == "asc" else "desc"

    where_clauses = []
    params = []

    if q:
        where_clauses.append("(p.nombre LIKE %s OR p.descripcion LIKE %s)")
        like_q = f"%{q}%"
        params.extend([like_q, like_q])

    if marca_id:
        try:
            where_clauses.append("p.marca_id = %s")
            params.append(int(marca_id))
        except ValueError:
            pass

    if categoria_id:
        try:
            where_clauses.append("p.categoria_id = %s")
            params.append(int(categoria_id))
        except ValueError:
            pass

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
    offset = (page - 1) * page_size

    sql_count = f"""
        SELECT COUNT(*) AS total
          FROM productos p
          {where_sql}
    """
    sql_data = f"""
        SELECT p.id, p.nombre, p.descripcion, p.precio, p.stock,
               p.marca_id AS marcaId, p.categoria_id AS categoriaId,
               p.created_at, p.updated_at
          FROM productos p
          {where_sql}
         ORDER BY {sort_by} {sort_dir}
         LIMIT %s OFFSET %s
    """

    try:
        conn = mysql.connector.connect(**db_config)

        cur = conn.cursor(dictionary=True)
        cur.execute(sql_count, params)
        total = cur.fetchone()["total"]
        cur.close()

        cur = conn.cursor(dictionary=True)
        cur.execute(sql_data, params + [page_size, offset])
        rows = cur.fetchall()
        cur.close()
        conn.close()

        total_pages = (total + page_size - 1) // page_size

        return jsonify({
            "status": "success",
            "meta": {
                "page": page,
                "pageSize": page_size,
                "total": total,
                "totalPages": total_pages
            },
            "data": rows
        }), 200

    except mysql.connector.Error as e:
        return jsonify({"status": "error", "message": f"DB error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ---------- CREAR PRODUCTO ----------
@app.post("/productos")
def create_producto():
    try:
        body = request.get_json(silent=True) or {}

        nombre = (body.get("nombre") or "").strip()
        precio = body.get("precio")
        stock = body.get("stock")
        marca_id = body.get("marcaId")
        categoria_id = body.get("categoriaId")

        errores = []
        if not nombre:
            errores.append("El nombre es obligatorio.")

        try:
            precio = float(precio)
            if precio < 0:
                errores.append("El precio no puede ser negativo.")
        except (TypeError, ValueError):
            errores.append("El precio debe ser numérico.")

        try:
            stock = int(stock)
            if stock < 0:
                errores.append("El stock no puede ser negativo.")
        except (TypeError, ValueError):
            errores.append("El stock debe ser un entero.")

        if errores:
            return jsonify({"status": "error", "message": "; ".join(errores)}), 400

        conn = mysql.connector.connect(**db_config)
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO productos (nombre, precio, stock, marca_id, categoria_id)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (nombre, precio, stock, marca_id, categoria_id)
        )
        conn.commit()
        nuevo_id = cur.lastrowid
        cur.close()
        conn.close()

        return jsonify({
            "status": "success",
            "data": {
                "id": nuevo_id,
                "nombre": nombre,
                "precio": precio,
                "stock": stock,
                "marcaId": marca_id,
                "categoriaId": categoria_id
            }
        }), 201

    except mysql.connector.Error as e:
        return jsonify({"status": "error", "message": f"DB error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ---------- OBTENER PRODUCTO POR ID ----------
@app.get("/productos/<int:pid>")
def get_producto(pid):
    conn = mysql.connector.connect(**db_config)
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM productos WHERE id = %s", (pid,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        return jsonify({"status": "error", "message": "Producto no encontrado"}), 404
    return jsonify({"status": "success", "data": row}), 200

# ---------- ACTUALIZAR PRODUCTO ----------
@app.put("/productos/<int:pid>")
def update_producto(pid):
    try:
        body = request.get_json(silent=True) or {}

        conn = mysql.connector.connect(**db_config)
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM productos WHERE id = %s", (pid,))
        actual = cur.fetchone()
        if not actual:
            cur.close()
            conn.close()
            return jsonify({"status": "error", "message": "Producto no encontrado"}), 404

        nombre = (body.get("nombre") or actual["nombre"]).strip()
        precio = body.get("precio", actual["precio"])
        stock = body.get("stock", actual["stock"])
        marca_id = body.get("marcaId", actual.get("marca_id"))
        categoria_id = body.get("categoriaId", actual.get("categoria_id"))

        errores = []
        if not nombre:
            errores.append("El nombre es obligatorio.")
        try:
            precio = float(precio)
            if precio < 0:
                errores.append("El precio no puede ser negativo.")
        except (TypeError, ValueError):
            errores.append("El precio debe ser numérico.")
        try:
            stock = int(stock)
            if stock < 0:
                errores.append("El stock no puede ser negativo.")
        except (TypeError, ValueError):
            errores.append("El stock debe ser un entero.")
        if errores:
            cur.close()
            conn.close()
            return jsonify({"status": "error", "message": "; ".join(errores)}), 400

        upd = conn.cursor()
        upd.execute(
            """
            UPDATE productos
               SET nombre=%s, precio=%s, stock=%s, marca_id=%s, categoria_id=%s
             WHERE id=%s
            """,
            (nombre, precio, stock, marca_id, categoria_id, pid)
        )
        conn.commit()
        upd.close()
        cur.close()
        conn.close()

        return jsonify({
            "status": "success",
            "data": {
                "id": pid, "nombre": nombre, "precio": precio, "stock": stock,
                "marcaId": marca_id, "categoriaId": categoria_id
            }
        }), 200

    except mysql.connector.Error as e:
        return jsonify({"status": "error", "message": f"DB error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ---------- ELIMINAR PRODUCTO ----------
@app.delete("/productos/<int:pid>")
def delete_producto(pid):
    try:
        conn = mysql.connector.connect(**db_config)
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM productos WHERE id=%s", (pid,))
        existe = cur.fetchone()
        if not existe:
            cur.close()
            conn.close()
            return jsonify({"status": "error", "message": "Producto no encontrado"}), 404

        cur.execute("DELETE FROM productos WHERE id=%s", (pid,))
        conn.commit()
        cur.close()
        conn.close()

        # Para que el front vea un mensaje, devolvemos 200 (no 204)
        return jsonify({"status": "success", "message": "Producto eliminado"}), 200

    except mysql.connector.Error as e:
        return jsonify({"status": "error", "message": f"DB error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ---------- MARCAS y CATEGORÍAS (para selects del Front) ----------
@app.get("/marcas")
def get_marcas():
    conn = mysql.connector.connect(**db_config)
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT id, nombre FROM marcas ORDER BY nombre ASC")
    data = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify({"status": "success", "data": data}), 200

@app.get("/categorias")
def get_categorias():
    conn = mysql.connector.connect(**db_config)
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT id, nombre FROM categorias ORDER BY nombre ASC")
    data = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify({"status": "success", "data": data}), 200

# ---------- RUN ----------
if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
