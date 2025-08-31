from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
import os

from autenticacion import auth_bp
from productos import products_bp
from categorias import categories_bp
from utils import ok

load_dotenv()

app = Flask(__name__)
CORS(app)
app.config["JWT_SECRET_KEY"] = os.getenv("FLASK_SECRET", "changeme")
jwt = JWTManager(app)

@app.get("/")
def home():
    return "¡Hola, backend funcionando!"

@app.get("/health")
def health():
    return ok({"status":"ok"})  # 200

# Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(products_bp)
app.register_blueprint(categories_bp)

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
