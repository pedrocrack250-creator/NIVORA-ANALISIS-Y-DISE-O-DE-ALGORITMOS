#pip install -r requirements.txt
import os
import tempfile

from flask import Flask, render_template, request
from controllers.aprender_controller import aprender_bp
from controllers.auth_controller import auth_bp
from controllers.laboratorio_controller import laboratorio_bp
from controllers.progreso_controller import progreso_bp
from config import Config
from errors.handlers import register_error_handlers
from security import csrf_token, validate_csrf


def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)

    # Cada instancia de pruebas usa su propia base temporal y no contamina
    # la base local del desarrollador ni otras pruebas.
    if app.config.get("TESTING") and not app.config.get("DATABASE_PATH"):
        descriptor, database_path = tempfile.mkstemp(prefix="nivora_test_", suffix=".db")
        os.close(descriptor)
        app.config["DATABASE_PATH"] = database_path

    # No regenerar la clave en cada arranque: hacerlo invalida las sesiones
    # y además ignoraba NIVORA_SECRET_KEY configurada por el despliegue.
    app.jinja_env.globals["csrf_token"] = csrf_token

    @app.before_request
    def protect_state_changing_requests():
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            validate_csrf(request.form.get("csrf_token"))

    @app.after_request
    def add_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        return response

    app.register_blueprint(aprender_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(laboratorio_bp)
    app.register_blueprint(progreso_bp)
    register_error_handlers(app)

    @app.route('/')
    def home():
        return render_template('index.html')

    @app.get('/health')
    def health():
        return {"status": "ok"}

    return app


app = create_app()


if __name__ == '__main__':
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1", port=int(os.environ.get("PORT", "5000")))