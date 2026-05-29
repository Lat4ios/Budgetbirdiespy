from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import json
import os
from functools import wraps

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Admin credentials (change these!)
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'golfadmin123'

# Path to data file
DATA_FILE = os.path.join(os.path.dirname(__file__), 'data', 'products.json')

def load_data():
    """Load data from JSON file"""
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
    """Save data to JSON file"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def admin_required(f):
    """Decorator to require admin login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            flash('Logged in successfully!', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid credentials!', 'error')
    
    return render_template('admin/login.html')

@admin_bp.route('/logout')
def logout():
    """Admin logout"""
    session.pop('admin_logged_in', None)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('admin.login'))

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Admin dashboard"""
    data = load_data()
    stats = {
        'total_products': len(data['products']),
        'total_features': len(data['features']),
        'low_stock': sum(1 for p in data['products'] if not p.get('inStock', True)),
        'total_value': sum(p['price'] for p in data['products'])
    }
    return render_template('admin/dashboard.html', stats=stats)

@admin_bp.route('/products')
@admin_required
def manage_products():
    """Manage products page"""
    data = load_data()
    return render_template('admin/products.html', products=data['products'])

@admin_bp.route('/products/add', methods=['POST'])
@admin_required
def add_product():
    """Add new product"""
    data = load_data()
    
    new_id = max([p['id'] for p in data['products']]) + 1 if data['products'] else 1
    
    new_product = {
        "id": new_id,
        "name": request.form.get('name'),
        "desc": request.form.get('desc'),
        "price": int(request.form.get('price')),
        "emoji": request.form.get('emoji'),
        "badge": request.form.get('badge', ''),
        "inStock": request.form.get('inStock') == 'on'
    }
    
    data['products'].append(new_product)
    save_data(data)
    flash('Product added successfully!', 'success')
    return redirect(url_for('admin.manage_products'))

@admin_bp.route('/products/edit/<int:product_id>', methods=['POST'])
@admin_required
def edit_product(product_id):
    """Edit existing product"""
    data = load_data()
    
    for product in data['products']:
        if product['id'] == product_id:
            product['name'] = request.form.get('name')
            product['desc'] = request.form.get('desc')
            product['price'] = int(request.form.get('price'))
            product['emoji'] = request.form.get('emoji')
            product['badge'] = request.form.get('badge', '')
            product['inStock'] = request.form.get('inStock') == 'on'
            break
    
    save_data(data)
    flash('Product updated successfully!', 'success')
    return redirect(url_for('admin.manage_products'))

@admin_bp.route('/products/delete/<int:product_id>')
@admin_required
def delete_product(product_id):
    """Delete product"""
    data = load_data()
    data['products'] = [p for p in data['products'] if p['id'] != product_id]
    save_data(data)
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('admin.manage_products'))

@admin_bp.route('/features')
@admin_required
def manage_features():
    """Manage features page"""
    data = load_data()
    return render_template('admin/features.html', features=data['features'])

@admin_bp.route('/features/edit/<int:feature_id>', methods=['POST'])
@admin_required
def edit_feature(feature_id):
    """Edit feature"""
    data = load_data()
    
    for feature in data['features']:
        if feature['id'] == feature_id:
            feature['title'] = request.form.get('title')
            feature['description'] = request.form.get('description')
            feature['icon'] = request.form.get('icon')
            break
    
    save_data(data)
    flash('Feature updated successfully!', 'success')
    return redirect(url_for('admin.manage_features'))

@admin_bp.route('/settings', methods=['GET', 'POST'])
@admin_required
def settings():
    """Site settings page"""
    data = load_data()
    
    if request.method == 'POST':
        data['site_settings'] = {
            "hero_title": request.form.get('hero_title'),
            "hero_subtitle": request.form.get('hero_subtitle'),
            "contact_email": request.form.get('contact_email'),
            "contact_phone": request.form.get('contact_phone'),
            "facebook_contact": request.form.get('facebook_contact')
        }
        save_data(data)
        flash('Settings updated successfully!', 'success')
        return redirect(url_for('admin.settings'))
    
    return render_template('admin/settings.html', settings=data['site_settings'])