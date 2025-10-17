from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_required, current_user
from app import db
from app.models.invoice import Invoice

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Landing page"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard showing invoice history with search and filters"""
    # Get filter parameters
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    status = request.args.get('status', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    sort_by = request.args.get('sort_by', 'created_at')
    sort_order = request.args.get('sort_order', 'desc')
    
    # Base query
    if current_user.is_admin():
        query = Invoice.query
    else:
        query = Invoice.query.filter_by(user_id=current_user.id)
    
    # Apply search filter
    if search:
        query = query.filter(
            db.or_(
                Invoice.invoice_number.ilike(f'%{search}%'),
                Invoice.vendor_name.ilike(f'%{search}%'),
                Invoice.customer_name.ilike(f'%{search}%')
            )
        )
    
    # Apply category filter
    if category:
        query = query.filter_by(category=category)
    
    # Apply status filter
    if status:
        query = query.filter_by(status=status)
    
    # Apply date range filter
    if date_from:
        query = query.filter(Invoice.invoice_date >= date_from)
    if date_to:
        query = query.filter(Invoice.invoice_date <= date_to)
    
    # Apply sorting
    if sort_order == 'asc':
        query = query.order_by(getattr(Invoice, sort_by).asc())
    else:
        query = query.order_by(getattr(Invoice, sort_by).desc())
    
    invoices = query.all()
    
    # Get unique categories for filter dropdown
    categories = db.session.query(Invoice.category).distinct().all()
    categories = [c[0] for c in categories if c[0]]
    
    return render_template('dashboard.html', invoices=invoices, categories=categories)
