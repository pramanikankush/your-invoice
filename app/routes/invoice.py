from flask import Blueprint, render_template, request, flash, redirect, url_for, send_file, session
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models.invoice import Invoice
from app.utils.gemini_extractor import extract_invoice_data
from app.utils.excel_exporter import export_to_excel
import os
import hashlib
from datetime import datetime

invoice_bp = Blueprint('invoice', __name__, url_prefix='/invoice')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_secure_filename(filename):
    """Generate hashed filename for security"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    hash_object = hashlib.md5(f"{filename}{timestamp}".encode())
    ext = filename.rsplit('.', 1)[1].lower()
    return f"{hash_object.hexdigest()}.{ext}"

@invoice_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    """Upload and process invoice"""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file uploaded', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            flash('No file selected', 'danger')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            # Generate secure filename
            original_filename = secure_filename(file.filename)
            secure_name = generate_secure_filename(original_filename)
            
            # Save file
            upload_folder = os.path.join(os.getcwd(), 'app', 'static', 'uploads')
            os.makedirs(upload_folder, exist_ok=True)
            file_path = os.path.join(upload_folder, secure_name)
            file.save(file_path)
            
            try:
                # Get API key from session
                api_key = session.get('gemini_api_key')
                if not api_key:
                    flash('API key not found. Please logout and login again with your API key.', 'danger')
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    return redirect(url_for('auth.logout'))
                
                # Extract data using Gemini AI
                extracted_data = extract_invoice_data(file_path, api_key)
                
                # Save to database
                invoice = Invoice(
                    user_id=current_user.id,
                    filename=original_filename,
                    file_path=secure_name,
                    invoice_number=extracted_data.get('invoice_number'),
                    invoice_date=extracted_data.get('invoice_date'),
                    vendor_name=extracted_data.get('vendor_name'),
                    vendor_address=extracted_data.get('vendor_address'),
                    customer_name=extracted_data.get('customer_name'),
                    customer_address=extracted_data.get('customer_address'),
                    subtotal=extracted_data.get('subtotal'),
                    tax_amount=extracted_data.get('tax_amount'),
                    total_amount=extracted_data.get('total_amount')
                )
                invoice.set_items(extracted_data.get('items', []))
                
                db.session.add(invoice)
                db.session.commit()
                
                flash('Invoice processed successfully!', 'success')
                return redirect(url_for('invoice.view', invoice_id=invoice.id))
            
            except Exception as e:
                flash(f'Error processing invoice: {str(e)}', 'danger')
                # Clean up uploaded file on error
                if os.path.exists(file_path):
                    os.remove(file_path)
                return redirect(request.url)
        else:
            flash('Invalid file type. Allowed: PNG, JPG, JPEG, PDF', 'danger')
    
    return render_template('upload.html')

@invoice_bp.route('/view/<int:invoice_id>')
@login_required
def view(invoice_id):
    """View invoice details"""
    invoice = Invoice.query.get_or_404(invoice_id)
    
    # Check access permission
    if not current_user.is_admin() and invoice.user_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('main.dashboard'))
    
    return render_template('invoice_view.html', invoice=invoice)

@invoice_bp.route('/delete/<int:invoice_id>', methods=['POST'])
@login_required
def delete(invoice_id):
    """Delete invoice"""
    try:
        invoice = Invoice.query.get_or_404(invoice_id)
        
        # Check permission
        if not current_user.is_admin() and invoice.user_id != current_user.id:
            flash('Access denied', 'danger')
            return redirect(url_for('main.dashboard'))
        
        # Store file path before deleting from DB
        file_path = os.path.join(os.getcwd(), 'app', 'static', 'uploads', invoice.file_path)
        
        # Delete from database first
        db.session.delete(invoice)
        db.session.commit()
        
        # Then delete file
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            pass  # File deletion error shouldn't stop the process
        
        flash('Invoice deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting invoice: {str(e)}', 'danger')
    
    return redirect(url_for('main.dashboard'))

@invoice_bp.route('/export/<int:invoice_id>')
@login_required
def export(invoice_id):
    """Export single invoice to Excel"""
    invoice = Invoice.query.get_or_404(invoice_id)
    
    # Check permission
    if not current_user.is_admin() and invoice.user_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('main.dashboard'))
    
    excel_file = export_to_excel([invoice])
    return send_file(excel_file, as_attachment=True, download_name=f'invoice_{invoice_id}.xlsx')

@invoice_bp.route('/export-all')
@login_required
def export_all():
    """Export all user invoices to Excel"""
    if current_user.is_admin():
        invoices = Invoice.query.all()
    else:
        invoices = Invoice.query.filter_by(user_id=current_user.id).all()
    
    if not invoices:
        flash('No invoices to export', 'warning')
        return redirect(url_for('main.dashboard'))
    
    excel_file = export_to_excel(invoices)
    return send_file(excel_file, as_attachment=True, download_name='all_invoices.xlsx')

@invoice_bp.route('/edit/<int:invoice_id>', methods=['GET', 'POST'])
@login_required
def edit(invoice_id):
    """Edit invoice details"""
    invoice = Invoice.query.get_or_404(invoice_id)
    
    if not current_user.is_admin() and invoice.user_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        invoice.invoice_number = request.form.get('invoice_number')
        invoice.invoice_date = request.form.get('invoice_date')
        invoice.vendor_name = request.form.get('vendor_name')
        invoice.vendor_address = request.form.get('vendor_address')
        invoice.customer_name = request.form.get('customer_name')
        invoice.customer_address = request.form.get('customer_address')
        invoice.subtotal = request.form.get('subtotal')
        invoice.tax_amount = request.form.get('tax_amount')
        invoice.total_amount = request.form.get('total_amount')
        invoice.category = request.form.get('category', 'Uncategorized')
        invoice.status = request.form.get('status', 'Processed')
        
        db.session.commit()
        flash('Invoice updated successfully', 'success')
        return redirect(url_for('invoice.view', invoice_id=invoice.id))
    
    return render_template('invoice_edit.html', invoice=invoice)

@invoice_bp.route('/bulk-upload', methods=['GET', 'POST'])
@login_required
def bulk_upload():
    """Upload multiple invoices at once"""
    if request.method == 'POST':
        files = request.files.getlist('files')
        
        if not files or files[0].filename == '':
            flash('No files selected', 'danger')
            return redirect(request.url)
        
        success_count = 0
        error_count = 0
        
        for file in files:
            if file and allowed_file(file.filename):
                try:
                    original_filename = secure_filename(file.filename)
                    secure_name = generate_secure_filename(original_filename)
                    
                    upload_folder = os.path.join(os.getcwd(), 'app', 'static', 'uploads')
                    os.makedirs(upload_folder, exist_ok=True)
                    file_path = os.path.join(upload_folder, secure_name)
                    file.save(file_path)
                    
                    api_key = session.get('gemini_api_key')
                    if not api_key:
                        continue
                    extracted_data = extract_invoice_data(file_path, api_key)
                    
                    invoice = Invoice(
                        user_id=current_user.id,
                        filename=original_filename,
                        file_path=secure_name,
                        invoice_number=extracted_data.get('invoice_number'),
                        invoice_date=extracted_data.get('invoice_date'),
                        vendor_name=extracted_data.get('vendor_name'),
                        vendor_address=extracted_data.get('vendor_address'),
                        customer_name=extracted_data.get('customer_name'),
                        customer_address=extracted_data.get('customer_address'),
                        subtotal=extracted_data.get('subtotal'),
                        tax_amount=extracted_data.get('tax_amount'),
                        total_amount=extracted_data.get('total_amount')
                    )
                    invoice.set_items(extracted_data.get('items', []))
                    db.session.add(invoice)
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    if os.path.exists(file_path):
                        os.remove(file_path)
        
        db.session.commit()
        flash(f'Uploaded {success_count} invoices successfully. {error_count} failed.', 'success' if error_count == 0 else 'warning')
        return redirect(url_for('main.dashboard'))
    
    return render_template('bulk_upload.html')

@invoice_bp.route('/bulk-delete', methods=['POST'])
@login_required
def bulk_delete():
    """Delete multiple invoices"""
    invoice_ids = request.form.getlist('invoice_ids')
    
    if not invoice_ids:
        flash('No invoices selected', 'warning')
        return redirect(url_for('main.dashboard'))
    
    deleted_count = 0
    file_paths = []
    
    try:
        for invoice_id in invoice_ids:
            invoice = Invoice.query.get(invoice_id)
            if invoice and (current_user.is_admin() or invoice.user_id == current_user.id):
                file_path = os.path.join(os.getcwd(), 'app', 'static', 'uploads', invoice.file_path)
                file_paths.append(file_path)
                db.session.delete(invoice)
                deleted_count += 1
        
        db.session.commit()
        
        # Delete files after successful DB commit
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception:
                pass
        
        flash(f'Deleted {deleted_count} invoices', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting invoices: {str(e)}', 'danger')
    
    return redirect(url_for('main.dashboard'))

@invoice_bp.route('/bulk-categorize', methods=['POST'])
@login_required
def bulk_categorize():
    """Categorize multiple invoices"""
    invoice_ids = request.form.getlist('invoice_ids')
    category = request.form.get('category', 'Uncategorized')
    
    if not invoice_ids:
        flash('No invoices selected', 'warning')
        return redirect(url_for('main.dashboard'))
    
    updated_count = 0
    for invoice_id in invoice_ids:
        invoice = Invoice.query.get(invoice_id)
        if invoice and (current_user.is_admin() or invoice.user_id == current_user.id):
            invoice.category = category
            updated_count += 1
    
    db.session.commit()
    flash(f'Categorized {updated_count} invoices', 'success')
    return redirect(url_for('main.dashboard'))

@invoice_bp.route('/reprocess/<int:invoice_id>', methods=['POST'])
@login_required
def reprocess(invoice_id):
    """Re-process invoice with AI"""
    invoice = Invoice.query.get_or_404(invoice_id)
    
    if not current_user.is_admin() and invoice.user_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('main.dashboard'))
    
    try:
        file_path = os.path.join(os.getcwd(), 'app', 'static', 'uploads', invoice.file_path)
        api_key = session.get('gemini_api_key')
        if not api_key:
            flash('API key not found. Please logout and login again.', 'danger')
            return redirect(url_for('auth.logout'))
        extracted_data = extract_invoice_data(file_path, api_key)
        
        invoice.invoice_number = extracted_data.get('invoice_number')
        invoice.invoice_date = extracted_data.get('invoice_date')
        invoice.vendor_name = extracted_data.get('vendor_name')
        invoice.vendor_address = extracted_data.get('vendor_address')
        invoice.customer_name = extracted_data.get('customer_name')
        invoice.customer_address = extracted_data.get('customer_address')
        invoice.subtotal = extracted_data.get('subtotal')
        invoice.tax_amount = extracted_data.get('tax_amount')
        invoice.total_amount = extracted_data.get('total_amount')
        invoice.set_items(extracted_data.get('items', []))
        
        db.session.commit()
        flash('Invoice reprocessed successfully', 'success')
    except Exception as e:
        flash(f'Error reprocessing invoice: {str(e)}', 'danger')
    
    return redirect(url_for('invoice.view', invoice_id=invoice.id))
