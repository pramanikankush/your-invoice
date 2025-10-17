from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(UserMixin, db.Model):
    """User model - API keys never stored in database"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    invoices = db.relationship('Invoice', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        self._session_api_key = None
    
    @property
    def gemini_api_key(self):
        """Get API key from session only - never stored"""
        return getattr(self, '_session_api_key', None)
    
    @gemini_api_key.setter
    def gemini_api_key(self, api_key):
        """Store API key in memory only - cleared on logout"""
        if api_key and isinstance(api_key, str) and len(api_key) >= 30:
            self._session_api_key = api_key.strip()
        else:
            self._session_api_key = None
    
    def has_api_key(self):
        """Check if user has API key in current session"""
        return bool(getattr(self, '_session_api_key', None))
    
    def clear_api_key(self):
        """Clear API key from memory"""
        self._session_api_key = None
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password"""
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        """Check if user is admin"""
        return self.role == 'admin'
    
    def __repr__(self):
        return f'<User {self.username}>'
