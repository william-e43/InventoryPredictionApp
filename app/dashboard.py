from .models import Order, Product, InventoryLevel, InventoryItem, Variant, LineItem
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
    app.logger.info(f"Starting calculate_avg_daily_sales for product: {product.id}, shop: {shop}")
    try:
        start_date = datetime.now() - timedelta(days=period_days)
        line_items = LineItem.query.join(Order).filter(
            LineItem.product_id == product.id,
            Order.shop == shop,
            Order.created_at >= start_date
        ).all()

        total_quantity = sum(item.quantity for item in line_items)
        days_with_sales = (datetime.now() - start_date).days or 1
        avg_daily_sales = total_quantity / days_with_sales
        app.logger.info(f"Average daily sales for product {product.id}: {avg_daily_sales}")
        return avg_daily_sales
    except Exception as e:
        app.logger.error(f"Error in calculate_avg_daily_sales for product {product.id}, shop {shop}: {str(e)}", exc_info=True)
        raise

def get_orders_data(shop, since_days=30):
    app.logger.info(f"Starting get_orders_data for shop: {shop}, since_days: {since_days} (type: {type(since_days)})")
    try:
        since_days = int(since_days)
        app.logger.info(f"Converted since_days to: {since_days} (type: {type(since_days)})")

        since_date = (datetime.now() - timedelta(days=since_days)).isoformat() + "Z"
        app.logger.info(f"Calculated since_date: {since_date}")

        orders = Order.query.filter(
            Order.shop == shop,
            Order.created_at >= datetime.now() - timedelta(days=since_days)
        ).all()

        daily_sales = {}
        for order in orders:
            for line_item in order.line_items:
                date_str = order.created_at.strftime('%Y-%m-%d')
                daily_sales[date_str] = daily_sales.get(date_str, 0) + line_item.quantity

        orders_data = [
            {
                'date': date,
                'sales': sales,
                'line_items': [
                    {'product_title': li.product_title, 'quantity': li.quantity}
                    for order in orders
                    for li in order.line_items
                    if order.created_at.strftime('%Y-%m-%d') == date
                ]
            }
            for date, sales in daily_sales.items()
        ]
        app.logger.info(f"Orders data processed: {orders_data}")
        return orders_data
    except Exception as e:
        app.logger.error(f"Error in get_orders_data for shop {shop}: {str(e)}", exc_info=True)
        raise

def get_inventory_data(shop):
    app.logger.info(f"Starting get_inventory_data for shop: {shop}")
    try:
        inventory_data = []
        for product in Product.query.all():
            inventory_data.append({
                'product': product.title,
                'stock': product.total_stock
            })
        app.logger.info(f"Inventory data processed: {inventory_data}")
        return inventory_data
    except Exception as e:
        app.logger.error(f"Error in get_inventory_data for shop {shop}: {str(e)}", exc_info=True)
        raise

def get_stock_predictions(shop):
    app.logger.info(f"Starting get_stock_predictions for shop: {shop}")
    try:
        days_of_cover = 30
        lead_time = 7

        app.logger.info(f"Days of cover: {days_of_cover} (type: {type(days_of_cover)})")
        app.logger.info(f"Lead time: {lead_time} (type: {type(lead_time)})")

        predictions = []
        for product in Product.query.all():
            avg_daily_sales = calculate_avg_daily_sales(product, shop)
            predicted_stock = product.total_stock - (avg_daily_sales * days_of_cover)  # Use total_stock
            restock_date = datetime.now() + timedelta(days=lead_time)
            predictions.append({
                'product': product.title,
                'predicted_stock': predicted_stock if predicted_stock > 0 else 0,
                'restock_date': restock_date
            })
        app.logger.info(f"Stock predictions fetched: {predictions}")
        return predictions
    except Exception as e:
        app.logger.error(f"Error in get_stock_predictions for shop {shop}: {str(e)}", exc_info=True)
        raise

def get_low_stock_alerts(shop):
    app.logger.info(f"Starting get_low_stock_alerts for shop: {shop}")
    try:

        days_of_cover = 30
        lead_time = 7

        app.logger.info(f"Days of cover: {days_of_cover} (type: {type(days_of_cover)})")
        app.logger.info(f"Lead time: {lead_time} (type: {type(lead_time)})")

        alerts = []
        for product in Product.query.all():
            stock = product.total_stock  # Use total_stock instead of quantity
            avg_daily_sales = calculate_avg_daily_sales(product, shop)
            days_remaining = stock / avg_daily_sales if avg_daily_sales > 0 else float('inf')
            if days_remaining < (days_of_cover + lead_time):
                alerts.append({
                    'product': product.title,
                    'days_remaining': days_remaining
                })
        app.logger.info(f"Low stock alerts fetched: {alerts}")
        return alerts
    except Exception as e:
        app.logger.error(f"Error in get_low_stock_alerts for shop {shop}: {str(e)}", exc_info=True)
        raise