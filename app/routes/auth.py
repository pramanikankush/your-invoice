from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models.user import User
import re
from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login with API key validation and rate limiting"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        if not _check_rate_limit():
            flash('Too many login attempts. Please try again later.', 'danger')
            return render_template('login.html'), 429
        
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        gemini_api_key = request.form.get('gemini_api_key', '').strip()
        
        if not email or not password:
            flash('Email and password are required', 'danger')
            return render_template('login.html')
        
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.check_password(password):
            _record_failed_attempt()
            flash('Invalid email or password', 'danger')
            return render_template('login.html')
        
        if not gemini_api_key:
            flash('Gemini API key is required', 'danger')
            return render_template('login.html')
        
        if not _validate_api_key(gemini_api_key):
            flash('Invalid Gemini API key format', 'danger')
            return render_template('login.html')
        
        session.permanent = True
        session['gemini_api_key'] = gemini_api_key
        login_user(user, remember=True)
        _clear_failed_attempts()
        
        flash('Login successful!', 'success')
        next_page = request.args.get('next')
        if next_page and _is_safe_url(next_page):
            return redirect(next_page)
        return redirect(url_for('main.dashboard'))
    
    return render_template('login.html')

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    """Registration disabled - single user system"""
    flash('Registration is disabled. Contact administrator.', 'danger')
    return redirect(url_for('auth.login'))
    


@auth_bp.route('/logout')
@login_required
def logout():
    """User logout with API key cleanup"""
    session.pop('gemini_api_key', None)
    session.clear()
    logout_user()
    flash('Logged out successfully. Please enter your API key again on next login.', 'info')
    return redirect(url_for('auth.login'))



def _validate_api_key(api_key):
    """Validate Gemini API key format"""
    if not api_key or not isinstance(api_key, str):
        return False
    if len(api_key) < 30 or len(api_key) > 100:
        return False
    if not api_key.startswith('AIzaSy'):
        return False
    return api_key.replace('-', '').replace('_', '').isalnum()

def _check_rate_limit():
    """Check rate limiting for login/signup attempts"""
    if 'attempts' not in session:
        session['attempts'] = []
    
    now = datetime.now()
    session['attempts'] = [t for t in session['attempts'] if now - datetime.fromisoformat(t) < timedelta(minutes=15)]
    
    if len(session['attempts']) >= 5:
        return False
    
    return True

def _record_failed_attempt():
    """Record failed login attempt"""
    if 'attempts' not in session:
        session['attempts'] = []
    session['attempts'].append(datetime.now().isoformat())
    session.modified = True

def _clear_failed_attempts():
    """Clear failed login attempts"""
    if 'attempts' in session:
        session.pop('attempts')

def _is_safe_url(target):
    """Check if redirect URL is safe"""
    from urllib.parse import urlparse, urljoin
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc
