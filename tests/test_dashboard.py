from app.dashboard import get_orders_data, get_inventory_data, get_low_stock_alerts, get_stock_prediction

def test_get_orders_data(app):
    with app[0].app_context():  # Use app[0] for the app instance
        daily_sales, top_products = get_orders_data()
        assert daily_sales is not None
        assert len(top_products) <= 5

def test_get_inventory_data(app):
    with app[0].app_context():  # Use app[0] for the app instance
        result = get_inventory_data(app[1])  # Use app[1] for the product_id
        assert "Total inventory: 5 units available" in result

def test_get_low_stock_alerts(app):
    with app[0].app_context():  # Use app[0] for the app instance
        result = get_low_stock_alerts()
        assert "<h2>Low Stock Alerts</h2>" in result
        assert "T-Shirt - Red" in result

def test_get_stock_prediction(app):
    with app[0].app_context():  # Use app[0] for the app instance
        _, top_products = get_orders_data()
        result = get_stock_prediction(top_products)
        assert "<h2>Stock Prediction</h2>" in result