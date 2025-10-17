from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os
import secrets

db = SQLAlchemy()
login_manager = LoginManager()

# Load from environment variables
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'ChangeMe123!')
SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_hex(32))

def create_app():
    app = Flask(__name__)
    
    app.config['SECRET_KEY'] = SECRET_KEY
    database_url = os.environ.get('DATABASE_URL', 'sqlite:///invoices.db')
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ECHO'] = False
    app.config['UPLOAD_FOLDER'] = 'app/static/uploads'
    app.config['MAX_CONTENT_LENGTH'] = 16777216
    app.config['SESSION_COOKIE_SECURE'] = False
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = 3600
    
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.session_protection = 'strong'
    
    @app.before_request
    def security_headers():
        if request.endpoint and 'static' not in request.endpoint:
            pass
    
    @app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data:;"
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        return response
    
    # Import models
    from app.models.user import User
    from app.models.invoice import Invoice
    
    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.invoice import invoice_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(invoice_bp)
    
    with app.app_context():
        try:
            db.create_all()
            _create_admin_user()
        except Exception as e:
            app.logger.error(f"Database initialization error: {e}")
    
    app.logger.info("Application initialized successfully")
    return app

def _create_admin_user():
    """Create admin user if not exists"""
    from app.models.user import User
    
    if not User.query.filter_by(email=ADMIN_EMAIL).first():
        admin = User(username='SecureAdmin', email=ADMIN_EMAIL, role='admin')
        admin.set_password(ADMIN_PASSWORD)
        db.session.add(admin)
        db.session.commit()
