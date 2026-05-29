from flask import Flask, render_template, request, session, redirect, url_for, jsonify, flash
import uuid
from datetime import datetime, timedelta
import json
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = 'golf-store-secret-key-2025'
app.permanent_session_lifetime = timedelta(days=7)

# Path to data file
DATA_FILE = os.path.join(os.path.dirname(__file__), 'data', 'products.json')

# Admin credentials
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'golfadmin123'

# Ensure data directory exists
os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)

# Initialize data file if it doesn't exist
def init_data_file():
    if not os.path.exists(DATA_FILE):
        initial_data = {
            "products": [
                {"id": 1, "name": "Premium Golf Balls (12 Pack)", "desc": "Tour-quality golf balls with exceptional distance and spin control.", "price": 2299, "emoji": "⚪", "badge": "Best Seller", "inStock": True},
                {"id": 2, "name": "Pro Driver", "desc": "Advanced aerodynamics for maximum distance off the tee.", "price": 18999, "emoji": "🏌️", "badge": "New", "inStock": True},
                {"id": 3, "name": "Tour Iron Set", "desc": "Precision-engineered irons for consistent ball striking.", "price": 45999, "emoji": "⛳", "badge": "Pro Choice", "inStock": True},
                {"id": 4, "name": "Blade Putter", "desc": "Milled face for pure roll and exceptional feel.", "price": 7999, "emoji": "🏌️‍♂️", "badge": "", "inStock": True},
                {"id": 5, "name": "Golf Stand Bag", "desc": "Lightweight with 5-way divider top.", "price": 5499, "emoji": "🎒", "badge": "", "inStock": True},
                {"id": 6, "name": "Performance Glove", "desc": "Premium cabretta leather for superior grip.", "price": 899, "emoji": "🧤", "badge": "Value Pack", "inStock": True}
            ],
            "features": [
                {"id": 1, "icon": "📦", "title": "Nationwide Shipping", "description": "We offer multiple couriers to ensure reliable and accessible delivery"},
                {"id": 2, "icon": "🔄", "title": "Easy Returns", "description": "Defective items can be replaced upon request"},
                {"id": 3, "icon": "🏆", "title": "Premium Quality", "description": "We ensure that every product meets our high standards and are all fairway ready"},
                {"id": 4, "icon": "💳", "title": "Flexible Payments", "description": "We accept COD, Bank Transfer, and E-Wallets"}
            ],
            "site_settings": {
                "hero_title": "Elevate Your Golf Game",
                "hero_subtitle": "Gear up for your next round with premium equipment trusted by pros",
                "contact_email": "support@fairwaygolf.com",
                "contact_phone": "(02) 1234 5678",
                "facebook_contact": "John Christian Llamas"
            }
        }
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f, indent=2, ensure_ascii=False)

init_data_file()

# Load data from JSON
def load_data():
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# Get products from JSON
def get_products():
    data = load_data()
    return data['products']

def get_product_by_id(product_id):
    products = get_products()
    for product in products:
        if product["id"] == product_id:
            return product
    return None

def get_features():
    data = load_data()
    return data['features']

def get_site_settings():
    data = load_data()
    return data['site_settings']

# Custom Jinja2 filter for number formatting
@app.template_filter('format_currency')
def format_currency(value):
    try:
        return f"{int(value):,}"
    except (ValueError, TypeError):
        return str(value)

# Make settings available to all templates
@app.context_processor
def inject_settings():
    return dict(settings=get_site_settings())

# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# ==================== PUBLIC ROUTES ====================

@app.route('/')
def index():
    products = get_products()
    features = get_features()
    return render_template('index.html', products=products[:3], features=features)

@app.route('/products')
def products():
    products = get_products()
    return render_template('products.html', products=products)

@app.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    product_id = int(request.form.get('product_id'))
    quantity = int(request.form.get('quantity', 1))
    
    if 'cart' not in session:
        session['cart'] = {}
    
    cart = dict(session['cart'])
    cart[str(product_id)] = cart.get(str(product_id), 0) + quantity
    session['cart'] = cart
    session.modified = True
    
    return redirect(request.referrer or url_for('products'))

@app.route('/update-cart', methods=['POST'])
def update_cart():
    product_id = str(request.form.get('product_id'))
    quantity = int(request.form.get('quantity', 0))
    
    cart = dict(session.get('cart', {}))
    
    if quantity <= 0:
        cart.pop(product_id, None)
    else:
        cart[product_id] = quantity
    
    session['cart'] = cart
    session.modified = True
    
    return redirect(url_for('cart'))

@app.route('/remove-from-cart', methods=['POST'])
def remove_from_cart():
    product_id = str(request.form.get('product_id'))
    
    cart = dict(session.get('cart', {}))
    cart.pop(product_id, None)
    session['cart'] = cart
    session.modified = True
    
    return redirect(url_for('cart'))

@app.route('/cart')
def cart():
    cart_items = []
    total = 0
    
    cart_data = session.get('cart', {})
    for product_id, quantity in cart_data.items():
        product = get_product_by_id(int(product_id))
        if product and product.get('inStock', True):
            item_total = product["price"] * quantity
            total += item_total
            cart_items.append({
                "product": product,
                "quantity": quantity,
                "item_total": item_total
            })
    
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/checkout')
def checkout():
    cart_items = []
    total = 0
    
    cart_data = session.get('cart', {})
    for product_id, quantity in cart_data.items():
        product = get_product_by_id(int(product_id))
        if product and product.get('inStock', True):
            item_total = product["price"] * quantity
            total += item_total
            cart_items.append({
                "product": product,
                "quantity": quantity,
                "item_total": item_total
            })
    
    if total == 0:
        return redirect(url_for('cart'))
    
    return render_template('checkout.html', cart_items=cart_items, total=total)

@app.route('/place-order', methods=['POST'])
def place_order():
    order_items = []
    total = 0
    
    cart_data = session.get('cart', {})
    for product_id, quantity in cart_data.items():
        product = get_product_by_id(int(product_id))
        if product:
            item_total = product["price"] * quantity
            total += item_total
            order_items.append({
                "name": product["name"],
                "price": product["price"],
                "quantity": quantity,
                "item_total": item_total
            })
    
    order = {
        "order_number": f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}",
        "full_name": request.form.get('full_name', ''),
        "email": request.form.get('email', ''),
        "phone": request.form.get('phone', ''),
        "address": request.form.get('address', ''),
        "city": request.form.get('city', ''),
        "province": request.form.get('province', ''),
        "zip": request.form.get('zip', ''),
        "payment_method": request.form.get('payment_method', 'COD'),
        "order_notes": request.form.get('order_notes', ''),
        "items": order_items,
        "total": total
    }
    
    session['last_order'] = order
    session.modified = True
    session['cart'] = {}
    session.modified = True
    
    return redirect(url_for('confirmation'))

@app.route('/confirmation')
def confirmation():
    order = session.get('last_order', {})
    
    if 'items' not in order or not isinstance(order['items'], list):
        order['items'] = []
    
    if not order.get('order_number'):
        order['order_number'] = 'ORD-NEW'
        order['total'] = 0
    
    return render_template('confirmation.html', order=order)

@app.route('/api/cart-count')
def cart_count():
    count = sum(session.get('cart', {}).values())
    return jsonify({"count": count})

# ==================== ADMIN ROUTES ====================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            flash('Logged in successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials!', 'error')
    
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    data = load_data()
    products = data['products']
    features = data['features']
    
    stats = {
        'total_products': len(products),
        'total_features': len(features),
        'out_of_stock': sum(1 for p in products if not p.get('inStock', True)),
        'total_value': sum(p['price'] for p in products)
    }
    return render_template('admin/dashboard.html', stats=stats)

@app.route('/admin/products')
@admin_required
def admin_products():
    data = load_data()
    return render_template('admin/products.html', products=data['products'])

@app.route('/admin/products/add', methods=['POST'])
@admin_required
def admin_add_product():
    data = load_data()
    products = data['products']
    
    new_id = max([p['id'] for p in products]) + 1 if products else 1
    
    new_product = {
        "id": new_id,
        "name": request.form.get('name'),
        "desc": request.form.get('desc'),
        "price": int(request.form.get('price')),
        "emoji": request.form.get('emoji'),
        "badge": request.form.get('badge', ''),
        "inStock": request.form.get('inStock') == 'on'
    }
    
    products.append(new_product)
    data['products'] = products
    save_data(data)
    flash('Product added successfully!', 'success')
    return redirect(url_for('admin_products'))

@app.route('/admin/products/edit/<int:product_id>', methods=['POST'])
@admin_required
def admin_edit_product(product_id):
    data = load_data()
    products = data['products']
    
    for product in products:
        if product['id'] == product_id:
            product['name'] = request.form.get('name')
            product['desc'] = request.form.get('desc')
            product['price'] = int(request.form.get('price'))
            product['emoji'] = request.form.get('emoji')
            product['badge'] = request.form.get('badge', '')
            product['inStock'] = request.form.get('inStock') == 'on'
            break
    
    data['products'] = products
    save_data(data)
    flash('Product updated successfully!', 'success')
    return redirect(url_for('admin_products'))

@app.route('/admin/products/delete/<int:product_id>')
@admin_required
def admin_delete_product(product_id):
    data = load_data()
    data['products'] = [p for p in data['products'] if p['id'] != product_id]
    save_data(data)
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('admin_products'))

@app.route('/admin/features')
@admin_required
def admin_features():
    data = load_data()
    return render_template('admin/features.html', features=data['features'])

@app.route('/admin/features/edit/<int:feature_id>', methods=['POST'])
@admin_required
def admin_edit_feature(feature_id):
    data = load_data()
    features = data['features']
    
    for feature in features:
        if feature['id'] == feature_id:
            feature['title'] = request.form.get('title')
            feature['description'] = request.form.get('description')
            feature['icon'] = request.form.get('icon')
            break
    
    data['features'] = features
    save_data(data)
    flash('Feature updated successfully!', 'success')
    return redirect(url_for('admin_features'))

@app.route('/admin/settings', methods=['GET', 'POST'])
@admin_required
def admin_settings():
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
        return redirect(url_for('admin_settings'))
    
    return render_template('admin/settings.html', settings=data['site_settings'])

# ==================== PRODUCTION SERVER ====================
if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)