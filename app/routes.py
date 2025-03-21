import shopify
import requests
from .config import Config
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, redirect, url_for, request, render_template, current_app as app
from .dashboard import get_orders_data, get_inventory_data, get_low_stock_alerts, get_stock_predictions
from .models import Order

bp = Blueprint('main', __name__)
session_data = {}  # In-memory storage for access tokens

# Root route
@bp.route("/")
def home():
    shop = request.args.get("shop")  # Check for shop in query string
    if shop and shop in session_data:
        return redirect(url_for('main.dashboard', shop=shop))
    elif session_data and list(session_data.keys()):
        default_shop = list(session_data.keys())[0]  # Use the last authenticated shop
        return redirect(url_for('main.dashboard', shop=default_shop))
    else:
        return redirect(url_for('main.install', shop="quickstart-c21ead54.myshopify.com"))

@bp.route("/install")
def install():
    shop = request.args.get("shop")
    if not shop:
        return jsonify({"error": "Missing shop parameter"}), 400

    if shop in session_data:
        return redirect(url_for('main.dashboard', shop=shop))

    shop = shop.replace("https://", "").replace("http://", "").rstrip("/")
    shop_url = f"https://{shop}"
    shopify.Session.setup(api_key=Config.API_KEY, secret=Config.API_SECRET)
    session = shopify.Session(shop_url, Config.API_VERSION)
    # Hardcode redirect_uri to match Shopify settings
    redirect_uri = "http://inventory-prediction-app.eba-p2hejcym.us-east-1.elasticbeanstalk.com/auth/callback"
    auth_url = session.create_permission_url(Config.SCOPES, redirect_uri)
    return redirect(auth_url)

# Callback route (unchanged)
@bp.route("/auth/callback")
def callback():
    params = request.args
    shop = params.get("shop")
    code = params.get("code")

    if not shop or not code:
        return jsonify({"error": "Missing shop or code parameter"}), 400

    shop_url = f"https://{shop}"

    try:
        token_url = f"{shop_url}/admin/oauth/access_token"
        payload = {
            "client_id": Config.API_KEY,
            "client_secret": Config.API_SECRET,
            "code": code
        }

        response = requests.post(token_url, data=payload)
        if response.status_code != 200:
            return jsonify({"error": f"Token exchange failed: {response.text}"}), 400

        token_data = response.json()
        access_token = token_data.get("access_token")
        if not access_token:
            return jsonify({"error": "No access token returned"}), 400

        associated_scopes = token_data.get("scope", "").split(",")
        expected_scopes = set(['read_orders', 'read_products', 'read_inventory'])
        if not all(scope in expected_scopes for scope in associated_scopes):
            print(f"Warning: Unexpected scopes returned: {associated_scopes}")

        session = shopify.Session(shop_url, Config.API_VERSION, access_token)
        session_data[shop] = {"access_token": access_token}
        return redirect(url_for('main.dashboard', shop=shop))

    except Exception as e:
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


@bp.route("/dashboard")
def dashboard():
    shop = request.args.get("shop")
    app.logger.info(f"Dashboard request received for shop: {shop}")

    if not shop:
        app.logger.error("Missing shop parameter in dashboard request")
        return jsonify({"error": "Missing shop parameter"}), 400

    if shop not in session_data:
        app.logger.info(f"Shop {shop} not in session_data, redirecting to install")
        return redirect(url_for('main.install', shop=shop))

    orders_data = None
    inventory_data = None
    low_stock_alerts = None
    stock_predictions = None

    try:
        app.logger.info(f"Fetching orders data for shop: {shop}")
        orders_data = get_orders_data(shop)
        app.logger.info(f"Orders data fetched: {orders_data}")
    except Exception as e:
        app.logger.error(f"Failed to fetch orders data for shop {shop}: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to fetch orders data", "details": str(e)}), 500

    try:
        app.logger.info(f"Fetching inventory data for shop: {shop}")
        inventory_data = get_inventory_data(shop)
        app.logger.info(f"Inventory data fetched: {inventory_data}")
    except Exception as e:
        app.logger.error(f"Failed to fetch inventory data for shop {shop}: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to fetch inventory data", "details": str(e)}), 500

    try:
        app.logger.info(f"Fetching low stock alerts for shop: {shop}")
        low_stock_alerts = get_low_stock_alerts(shop)
        app.logger.info(f"Low stock alerts fetched: {low_stock_alerts}")
    except Exception as e:
        app.logger.error(f"Failed to fetch low stock alerts for shop {shop}: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to fetch low stock alerts", "details": str(e)}), 500

    try:
        app.logger.info(f"Fetching stock predictions for shop: {shop}")
        stock_predictions = get_stock_predictions(shop)
        app.logger.info(f"Stock predictions fetched: {stock_predictions}")
    except Exception as e:
        app.logger.error(f"Failed to fetch stock predictions for shop {shop}: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to fetch stock predictions", "details": str(e)}), 500

    try:
        app.logger.info(f"Rendering dashboard for shop: {shop}")
        return render_template(
            "dashboard.html",
            shop=shop,
            orders_data=orders_data,
            inventory_data=inventory_data,
            low_stock_alerts=low_stock_alerts,
            stock_predictions=stock_predictions
        )
    except Exception as e:
        app.logger.error(f"Failed to render dashboard for shop {shop}: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to render dashboard", "details": str(e)}), 500
# def dashboard():
#     shop = request.args.get("shop")
#     if not shop or shop not in session_data:
#         return jsonify({"error": "Not authenticated. Please install the app."}), 401
#
#     try:
#         daily_sales, top_products = get_orders_data()
#         if not daily_sales:
#             return render_template("dashboard.html", dashboard_content="<h1>Inventory Prediction App Dashboard (Mock Data)</h1><p>No orders found in the last 60 days.</p>")
#
#         inventory_data = get_inventory_data(top_products[0][0] if top_products else None)
#         low_stock_alerts = get_low_stock_alerts()
#         stock_prediction = get_stock_prediction(top_products)
#
#         dashboard_content = ""
#         dashboard_content += "<h1>Inventory Prediction App Dashboard (Mock Data)</h1>"
#         dashboard_content += "<h2>Daily Sales (Last 60 Days)</h2><ul>"
#         for date, total in sorted(daily_sales.items()):
#             dashboard_content += f"<li>{date}: {total} units sold</li>"
#         dashboard_content += "</ul>"
#
#         dashboard_content += "<h2>Top Products by Sales Volume</h2><ul>"
#         for product_id, quantity in top_products:
#             product_title = next((item.product_title for order in Order.query.all() for item in order.line_items if item.product_id == product_id), "Unknown Product")
#             dashboard_content += f"<li>{product_title}: {quantity} units sold</li>"
#         dashboard_content += "</ul>"
#
#         dashboard_content += f"<h2>Inventory for Top Product</h2><p>{inventory_data}</p>"
#         dashboard_content += low_stock_alerts
#         dashboard_content += stock_prediction
#
#         return render_template("dashboard.html", dashboard_content=dashboard_content)
#
#     except Exception as e:
#         print(f"Exception in dashboard: {str(e)}")
#         error_response = jsonify({"error": "Failed to fetch dashboard data", "details": str(e)})
#         error_response.status_code = 500
#         return error_response