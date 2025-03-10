from .models import Order, Product, InventoryLevel, InventoryItem, Variant
from datetime import datetime, timedelta

def get_orders_data(since_days=60):
    """Fetch and aggregate order data for the last `since_days`."""
    since_date = (datetime.now() - timedelta(days=since_days)).isoformat() + "Z"
    orders = Order.query.filter(Order.created_at >= since_date).all()
    if not orders:
        return None, None

    daily_sales = {}
    product_sales = {}
    for order in orders:
        date = order.created_at[:10]
        line_items = order.line_items
        if not line_items:
            continue
        total_quantity = sum(float(item.quantity) for item in line_items)
        daily_sales[date] = daily_sales.get(date, 0) + total_quantity
        for item in line_items:
            product_sales[item.product_id] = product_sales.get(item.product_id, 0) + item.quantity
    return daily_sales, sorted(product_sales.items(), key=lambda x: x[1], reverse=True)[:5]

def get_inventory_data(top_product_id):
    """Fetch total inventory for the top product."""
    if not top_product_id:
        return "No inventory data available"
    product = Product.query.get(top_product_id)
    if product:
        total_inventory = sum(
            level.available for level in InventoryLevel.query
            .select_from(InventoryLevel)
            .join(InventoryItem, InventoryLevel.inventory_item_id == InventoryItem.id)
            .join(Variant, InventoryItem.variant_id == Variant.id)
            .filter(Variant.product_id == top_product_id).all()
        ) or 0
        return f"Total inventory: {total_inventory} units available"
    return "No inventory data available"

def get_low_stock_alerts(threshold=10):
    """Fetch and format low stock alerts."""
    low_stock_items = InventoryLevel.query.filter(InventoryLevel.available < threshold).all()
    if not low_stock_items:
        return ""
    alerts = "<h2>Low Stock Alerts</h2><ul>"
    for level in low_stock_items:
        variant = Variant.query.join(InventoryItem, InventoryItem.id == level.inventory_item_id).first()
        if variant:
            alerts += f"<li>{variant.title} (ID: {variant.id}): {level.available} units left</li>"
    alerts += "</ul>"
    return alerts

def get_stock_prediction(top_products):
    """Calculate stock prediction for the top product."""
    if not top_products:
        return ""
    top_product_id = top_products[0][0]
    total_days = 60
    total_quantity = sum(item.quantity for order in Order.query.all() for item in order.line_items if item.product_id == top_product_id)
    avg_daily_sales = total_quantity / total_days if total_days > 0 else 0
    inventory_level = InventoryLevel.query.select_from(InventoryLevel).join(InventoryItem, InventoryLevel.inventory_item_id == InventoryItem.id).join(Variant, InventoryItem.variant_id == Variant.id).join(Product, Variant.product_id == Product.id).filter(Product.id == top_product_id).first()
    days_to_deplete = inventory_level.available / avg_daily_sales if avg_daily_sales > 0 else float('inf')
    product_title = next((item.product_title for order in Order.query.all() for item in order.line_items if item.product_id == top_product_id), "Unknown Product")
    return f"<h2>Stock Prediction</h2><p>{product_title}: Approximately {days_to_deplete:.1f} days of stock remaining</p>"