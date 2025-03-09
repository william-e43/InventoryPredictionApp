import shopify
import requests
from .config import Config
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, redirect, url_for, request, render_template
import random
from .models import Order, Product, InventoryLevel, InventoryItem, Variant

bp = Blueprint('main', __name__)
session_data = {}  # In-memory storage for access tokens

# Root route
@bp.route("/")
def home():
    print("Root route called")
    shop = request.args.get("shop")  # Check for shop in query string
    if shop and shop in session_data:
        print(f"Redirecting to dashboard with shop: {shop}")
        return redirect(url_for('main.dashboard', shop=shop))
    elif session_data and list(session_data.keys()):
        default_shop = list(session_data.keys())[0]  # Use the last authenticated shop
        print(f"Redirecting to dashboard with default shop: {default_shop}")
        return redirect(url_for('main.dashboard', shop=default_shop))
    else:
        print("No authenticated shop found, redirecting to install")
        return redirect(url_for('main.install', shop="quickstart-c21ead54.myshopify.com"))

# Install route (unchanged)
@bp.route("/install")
def install():
    shop = request.args.get("shop")
    print(f"Install route called with shop: {shop}")
    if not shop:
        print("Error: Missing shop parameter")
        return jsonify({"error": "Missing shop parameter"}), 400

    if shop in session_data:
        print(f"Shop {shop} already authenticated, redirecting to dashboard")
        return redirect(url_for('main.dashboard', shop=shop))

    shop = shop.replace("https://", "").replace("http://", "").rstrip("/")
    shop_url = f"https://{shop}"
    print(f"Shop: {shop}, Shop URL: {shop_url}")
    print(f"Config.API_KEY: {Config.API_KEY}")
    print(f"Config.API_SECRET: {Config.API_SECRET}")
    print(f"Config.SCOPES: {Config.SCOPES}")
    print(f"Config.REDIRECT_URI: {Config.REDIRECT_URI}")
    print(f"Config.API_VERSION: {Config.API_VERSION}")

    shopify.Session.setup(api_key=Config.API_KEY, secret=Config.API_SECRET)
    session = shopify.Session(shop_url, Config.API_VERSION)
    auth_url = session.create_permission_url(Config.SCOPES, Config.REDIRECT_URI)
    print(f"Redirecting to Shopify auth URL: {auth_url}")
    return redirect(auth_url)

# Callback route (unchanged)
@bp.route("/auth/callback")
def callback():
    print("Callback route called")
    params = request.args
    shop = params.get("shop")
    code = params.get("code")

    print(f"Callback params: {params}")

    if not shop or not code:
        print("Error: Missing shop or code parameter")
        return jsonify({"error": "Missing shop or code parameter"}), 400

    shop_url = f"https://{shop}"
    print(f"Shop URL: {shop_url}")
    print(f"Config.API_KEY: {Config.API_KEY}")
    print(f"Config.API_SECRET: {Config.API_SECRET}")
    print(f"Config.API_VERSION: {Config.API_VERSION}")

    try:
        token_url = f"{shop_url}/admin/oauth/access_token"
        payload = {
            "client_id": Config.API_KEY,
            "client_secret": Config.API_SECRET,
            "code": code
        }

        print(f"Requesting token from: {token_url}")
        print(f"Token payload: {payload}")

        response = requests.post(token_url, data=payload)
        if response.status_code != 200:
            print(f"Token exchange failed: {response.status_code} - {response.text}")
            return jsonify({"error": f"Token exchange failed: {response.text}"}), 400

        token_data = response.json()
        access_token = token_data.get("access_token")
        if not access_token:
            print("Error: No access token returned")
            return jsonify({"error": "No access token returned"}), 400

        associated_scopes = token_data.get("scope", "").split(",")
        print(f"Access token: {access_token}")
        print(f"Associated scopes: {associated_scopes}")

        expected_scopes = set(['read_orders', 'read_products', 'read_inventory'])
        if not all(scope in expected_scopes for scope in associated_scopes):
            print(f"Warning: Unexpected scopes returned: {associated_scopes}")

        session = shopify.Session(shop_url, Config.API_VERSION, access_token)
        session_data[shop] = {"access_token": access_token}
        print(f"Stored access token for {shop} in session_data")
        return redirect(url_for('main.dashboard', shop=shop))

    except Exception as e:
        print(f"Exception during callback: {str(e)}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

@bp.route("/dashboard")
def dashboard():
    print("Dashboard route called")
    shop = request.args.get("shop")
    print(f"Shop: {shop}")
    print(f"Session data: {session_data}")
    if not shop or shop not in session_data:
        print("Error: Not authenticated - shop not in session_data")
        return jsonify({"error": "Not authenticated. Please install the app."}), 401

    try:
        # Initialize html string
        html = ""

        # Query mock order data from SQLite
        since_date = (datetime.now() - timedelta(days=60)).isoformat() + "Z"
        orders = Order.query.filter(Order.created_at >= since_date).all()

        if not orders:
            html = "<h1>Inventory Prediction App Dashboard (Mock Data)</h1><p>No orders found in the last 60 days.</p>"
            return html

        # Aggregate daily sales (using quantity as proxy)
        daily_sales = {}
        product_sales = {}
        for order in orders:
            date = order.created_at[:10]  # Extract YYYY-MM-DD
            line_items = order.line_items
            if not line_items:
                print(f"Warning: No line items for order {order.id}")
                continue
            total_quantity = sum(float(item.quantity) for item in line_items)
            daily_sales[date] = daily_sales.get(date, 0) + total_quantity

            for item in line_items:
                product_id = item.product_id
                quantity = item.quantity
                product_sales[product_id] = product_sales.get(product_id, 0) + quantity

        top_products = sorted(product_sales.items(), key=lambda x: x[1], reverse=True)[:5] if product_sales else []

        # Fetch inventory data for the top product
        top_product_id = top_products[0][0] if top_products else None
        inventory_data = "No inventory data available"
        if top_product_id:
            product = Product.query.get(top_product_id)
            if product:
                # Explicitly define the join path starting from InventoryLevel
                total_inventory = sum(
                    level.available for level in InventoryLevel.query
                    .select_from(InventoryLevel)
                    .join(InventoryItem, InventoryLevel.inventory_item_id == InventoryItem.id)
                    .join(Variant, InventoryItem.variant_id == Variant.id)
                    .filter(Variant.product_id == top_product_id).all()
                ) or 0
                inventory_data = f"Total inventory: {total_inventory} units available"

        # Add low stock alerts
        low_stock_items = InventoryLevel.query.filter(InventoryLevel.available < 10).all()
        if low_stock_items:
            html += "<h2>Low Stock Alerts</h2><ul>"
            for level in low_stock_items:
                # Use a subquery to fetch the variant for each low stock item
                variant = Variant.query.join(InventoryItem, InventoryItem.id == level.inventory_item_id).first()
                if variant:
                    html += f"<li>{variant.title} (ID: {variant.id}): {level.available} units left</li>"
            html += "</ul>"

        # Add stock prediction for the top product
        if top_products:
            top_product_id = top_products[0][0]
            total_days = 60  # Assuming 60-day window for simplicity
            total_quantity = sum(item.quantity for order in orders for item in order.line_items if item.product_id == top_product_id)
            avg_daily_sales = total_quantity / total_days if total_days > 0 else 0
            # Explicitly define the join path for stock prediction
            inventory_level = InventoryLevel.query.select_from(InventoryLevel).join(InventoryItem, InventoryLevel.inventory_item_id == InventoryItem.id).join(Variant, InventoryItem.variant_id == Variant.id).join(Product, Variant.product_id == Product.id).filter(Product.id == top_product_id).first()
            days_to_deplete = inventory_level.available / avg_daily_sales if avg_daily_sales > 0 else float('inf')
            product_title = next(item.product_title for order in orders for item in order.line_items if item.product_id == top_product_id)
            html += f"<h2>Stock Prediction</h2><p>{product_title}: Approximately {days_to_deplete:.1f} days of stock remaining</p>"

        # Display mock order and inventory data
        html += "<h1>Inventory Prediction App Dashboard (Mock Data)</h1>"
        html += "<h2>Daily Sales (Last 60 Days)</h2><ul>"
        for date, total in sorted(daily_sales.items()):
            html += f"<li>{date}: {total} units sold</li>"
        html += "</ul>"

        html += "<h2>Top Products by Sales Volume</h2><ul>"
        for product_id, quantity in top_products:
            product_title = next((item.product_title for order in orders for item in order.line_items if item.product_id == product_id), "Unknown Product")
            html += f"<li>{product_title}: {quantity} units sold</li>"
        html += "</ul>"

        html += f"<h2>Inventory for Top Product</h2><p>{inventory_data}</p>"

        return html

    except Exception as e:  # noqa: E722
        print(f"Exception in dashboard: {str(e)}")
        error_response = jsonify({"error": "Failed to fetch dashboard data", "details": str(e)})
        error_response.status_code = 500
        return error_response