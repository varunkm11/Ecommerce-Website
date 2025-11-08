from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from pricing.algorithm import PricingEngine
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "your-secret-key-change-in-production"  # Change this in production!

# Load sample products
products_path = os.path.join(os.path.dirname(__file__), "products.json")
with open(products_path, "r", encoding="utf-8") as f:
    PRODUCTS = json.load(f)

engine = PricingEngine(PRODUCTS)

# Helper function to get product by ID
def get_product_with_pricing(product_id):
    product = next((p for p in PRODUCTS if p["id"] == product_id), None)
    if product:
        rec = engine.recommend_price(product_id)
        item = dict(product)
        item.update(rec)
        return item
    return None


@app.route("/")
def index():
    """Main product catalog page"""
    category = request.args.get('category', 'all')
    
    recommendations = []
    for p in PRODUCTS:
        if category == 'all' or p.get('category', '').lower() == category.lower():
            rec = engine.recommend_price(p["id"]) 
            item = dict(p)
            item.update(rec)
            recommendations.append(item)
    
    # Get unique categories
    categories = list(set([p.get('category', 'Other') for p in PRODUCTS]))
    categories.sort()
    
    return render_template("index.html", products=recommendations, categories=categories, current_category=category)


@app.route("/product/<product_id>")
def product_detail(product_id):
    """Product detail page with full description"""
    product = get_product_with_pricing(product_id)
    if not product:
        return "Product not found", 404
    
    return render_template("product_detail.html", product=product)


@app.route("/cart")
def cart():
    """Shopping cart page"""
    cart_items = session.get('cart', {})
    items_with_data = []
    total = 0
    
    for product_id, quantity in cart_items.items():
        product = get_product_with_pricing(product_id)
        if product:
            product['quantity'] = quantity
            product['subtotal'] = product['recommended_price'] * quantity
            items_with_data.append(product)
            total += product['subtotal']
    
    return render_template("cart.html", items=items_with_data, total=total)


@app.route("/wishlist")
def wishlist():
    """Wishlist page"""
    wishlist_ids = session.get('wishlist', [])
    items = []
    
    for product_id in wishlist_ids:
        product = get_product_with_pricing(product_id)
        if product:
            items.append(product)
    
    return render_template("wishlist.html", items=items)


@app.route("/checkout")
def checkout():
    """Checkout page"""
    cart_items = session.get('cart', {})
    items_with_data = []
    subtotal = 0
    
    for product_id, quantity in cart_items.items():
        product = get_product_with_pricing(product_id)
        if product:
            product['quantity'] = quantity
            product['subtotal'] = product['recommended_price'] * quantity
            items_with_data.append(product)
            subtotal += product['subtotal']
    
    shipping = 99 if subtotal < 3000 else 0  # Free shipping over ₹3000
    tax = subtotal * 0.18  # 18% GST
    total = subtotal + shipping + tax
    
    return render_template("checkout.html", items=items_with_data, subtotal=subtotal, shipping=shipping, tax=tax, total=total)


@app.route("/order-success")
def order_success():
    """Order confirmation page"""
    # Clear cart after successful order
    session.pop('cart', None)
    return render_template("order_success.html")


# API Endpoints
@app.route("/api/recommendations")
def api_recommendations():
    data = {p["id"]: engine.recommend_price(p["id"]) for p in PRODUCTS}
    return jsonify(data)


@app.route("/api/cart/add", methods=['POST'])
def api_cart_add():
    """Add item to cart"""
    data = request.json
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    
    if 'cart' not in session:
        session['cart'] = {}
    
    cart = session['cart']
    cart[product_id] = cart.get(product_id, 0) + quantity
    session['cart'] = cart
    
    return jsonify({'success': True, 'cart_count': sum(session['cart'].values())})


@app.route("/api/cart/update", methods=['POST'])
def api_cart_update():
    """Update cart item quantity"""
    data = request.json
    product_id = data.get('product_id')
    quantity = data.get('quantity', 0)
    
    if 'cart' in session:
        cart = session['cart']
        if quantity <= 0:
            cart.pop(product_id, None)
        else:
            cart[product_id] = quantity
        session['cart'] = cart
    
    return jsonify({'success': True, 'cart_count': sum(session.get('cart', {}).values())})


@app.route("/api/cart/remove", methods=['POST'])
def api_cart_remove():
    """Remove item from cart"""
    data = request.json
    product_id = data.get('product_id')
    
    if 'cart' in session:
        cart = session['cart']
        cart.pop(product_id, None)
        session['cart'] = cart
    
    return jsonify({'success': True, 'cart_count': sum(session.get('cart', {}).values())})


@app.route("/api/wishlist/add", methods=['POST'])
def api_wishlist_add():
    """Add item to wishlist"""
    data = request.json
    product_id = data.get('product_id')
    
    if 'wishlist' not in session:
        session['wishlist'] = []
    
    wishlist = session['wishlist']
    if product_id not in wishlist:
        wishlist.append(product_id)
        session['wishlist'] = wishlist
    
    return jsonify({'success': True, 'wishlist_count': len(session['wishlist'])})


@app.route("/api/wishlist/remove", methods=['POST'])
def api_wishlist_remove():
    """Remove item from wishlist"""
    data = request.json
    product_id = data.get('product_id')
    
    if 'wishlist' in session:
        wishlist = session['wishlist']
        if product_id in wishlist:
            wishlist.remove(product_id)
            session['wishlist'] = wishlist
    
    return jsonify({'success': True, 'wishlist_count': len(session.get('wishlist', []))})


@app.route("/api/checkout/complete", methods=['POST'])
def api_checkout_complete():
    """Process checkout"""
    data = request.json
    # In a real app, you'd process payment, create order, update inventory, etc.
    # For now, we'll just clear the cart and return success
    
    session.pop('cart', None)
    return jsonify({'success': True, 'message': 'Order placed successfully!'})


if __name__ == "__main__":
    app.run(debug=True)
