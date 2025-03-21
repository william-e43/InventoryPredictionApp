from .models import Order, Product, InventoryLevel, InventoryItem, Variant
from datetime import datetime, timedelta
from flask import current_app as app


def calculate_avg_daily_sales(product, shop, period_days=30):
    """
    Calculate the average daily sales for a product over a specified period.

    Args:
        product: Product object (from app.models.Product)
        shop: Shopify shop domain (string)
        period_days: Number of days to consider for the average (default: 30)

    Returns:
        float: Average daily sales (quantity sold per day)
    """
    try:
        # Calculate the start date (e.g., 30 days ago)
        start_date = datetime.now() - timedelta(days=period_days)

        # Query orders for this product and shop within the period
        orders = Order.query.filter(
            Order.product_id == product.id,
            Order.shop == shop,
            Order.created_at >= start_date
        ).all()

        # Sum the quantities sold
        total_quantity = sum(order.quantity for order in orders)

        # Calculate average daily sales
        if total_quantity == 0:
            return 0.0

        # Number of days with sales (to avoid division by zero)
        days_with_sales = (datetime.now() - start_date).days
        if days_with_sales <= 0:
            days_with_sales = 1

        avg_daily_sales = total_quantity / days_with_sales
        return avg_daily_sales
    except Exception as e:
        app.logger.error(f"Error in calculate_avg_daily_sales for product {product.id}, shop {shop}: {str(e)}",exc_info=True)
        raise

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

def get_stock_prediction(shop):
    app.logger.info(f"Starting get_stock_predictions for shop: {shop}")
    try:
        # Example: Fetch settings (days_of_cover, lead_time)
        # settings = get_inventory_settings(shop)  # Hypothetical function
        days_of_cover = 30
        lead_time =  7

        app.logger.info(f"Days of cover: {days_of_cover} (type: {type(days_of_cover)})")
        app.logger.info(f"Lead time: {lead_time} (type: {type(lead_time)})")

        # Ensure integer conversion
        days_of_cover = int(days_of_cover)
        lead_time = int(lead_time)

        # Example prediction logic
        predictions = []
        for product in Product.query.all():
            avg_daily_sales = calculate_avg_daily_sales(product, shop)
            predicted_days = avg_daily_sales * days_of_cover
            restock_date = datetime.now() + timedelta(days=lead_time)
            predictions.append({
                'product': product.name,
                'predicted_days': predicted_days,
                'restock_date': restock_date
            })
        return predictions
    except Exception as e:
        app.logger.error(f"Error in get_stock_predictions for shop {shop}: {str(e)}", exc_info=True)
        raise

def get_low_stock_alerts(shop):
    app.logger.info(f"Starting get_low_stock_alerts for shop: {shop}")
    try:
        # settings = get_inventory_settings(shop)  # Hypothetical function
        days_of_cover = 30
        lead_time = 7

        app.logger.info(f"Days of cover: {days_of_cover} (type: {type(days_of_cover)})")
        app.logger.info(f"Lead time: {lead_time} (type: {type(lead_time)})")

        # Ensure integer conversion
        days_of_cover = int(days_of_cover)
        lead_time = int(lead_time)

        # Example alert logic
        alerts = []
        for product in Product.query.all():
            stock = product.quantity
            avg_daily_sales = calculate_avg_daily_sales(product, shop)
            days_remaining = stock / avg_daily_sales if avg_daily_sales > 0 else float('inf')
            if days_remaining < (days_of_cover + lead_time):
                alerts.append({
                    'product': product.name,
                    'days_remaining': days_remaining
                })
        return alerts
    except Exception as e:
        app.logger.error(f"Error in get_low_stock_alerts for shop {shop}: {str(e)}", exc_info=True)
        raise