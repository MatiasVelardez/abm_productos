# ABM Productos — Backend Flask

API REST en **Flask + MySQL** para gestionar productos, con CRUD completo (alta, baja, modificación y listado), además de búsqueda, filtros y paginación.

# 🚀 Requisitos

- Python 3.10 o superior  
- MySQL (XAMPP o similar) corriendo  
- Visual Studio Code (recomendado)  

## ⚙️ Instalación

# Clonar el repo o crear carpeta
cd abm-backend

# Crear entorno virtual
python -m venv venv

# Activar entorno
# Git Bash:
source venv/Scripts/activate
# CMD:
venv\Scripts\activate
# PowerShell:
venv\Scripts\Activate.ps1

# Instalar dependencias
pip install flask flask-cors mysql-connector-python

🗄️ Base de datos

Ejecutar en phpMyAdmin → pestaña SQL:

CREATE DATABASE IF NOT EXISTS abm_productos CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE abm_productos;

CREATE TABLE IF NOT EXISTS marcas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS categorias (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS productos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(120) NOT NULL,
    descripcion TEXT,
    precio DECIMAL(10,2) NOT NULL,
    stock INT NOT NULL,
    marca_id INT,
    categoria_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (marca_id) REFERENCES marcas(id),
    FOREIGN KEY (categoria_id) REFERENCES categorias(id)
);

INSERT INTO marcas (nombre) VALUES ("Arcor"), ("Nestlé"), ("Bagley");
INSERT INTO categorias (nombre) VALUES ("Chocolates"), ("Galletitas"), ("Caramelos");

▶️ Ejecutar servidor
python app.py

El backend queda disponible en:
👉 http://127.0.0.1:5000/

🔌 Endpoints principales

Productos
GET /productos — lista productos (con filtros, búsqueda y paginación)

GET /productos/:id — obtiene un producto por ID

POST /productos — crea un producto

PUT /productos/:id — actualiza un producto

DELETE /productos/:id — elimina un producto

Auxiliares
GET /marcas — devuelve lista de marcas

GET /categorias — devuelve lista de categorías

🧪 Ejemplos de uso
Crear producto

curl -X POST http://127.0.0.1:5000/productos \
  -H "Content-Type: application/json" \
  -d "{\"nombre\":\"Tita\",\"precio\":150.5,\"stock\":25,\"marcaId\":1,\"categoriaId\":2}"
  
Listar productos con búsqueda y orden

curl "http://127.0.0.1:5000/productos?q=choco&page=1&pageSize=5&sortBy=precio&sortDir=asc"

Actualizar producto

curl -X PUT http://127.0.0.1:5000/productos/1 \
  -H "Content-Type: application/json" \
  -d "{\"precio\":500,\"stock\":40}"

Eliminar producto

curl -X DELETE http://127.0.0.1:5000/productos/1
