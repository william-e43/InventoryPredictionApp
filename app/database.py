# app/database.py
import logging
from random import randint, choice
from flask import Flask
from .models import db, Order, LineItem, Product, Variant, InventoryItem, InventoryLevel
from .config import Config
from datetime import datetime, timedelta


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db(app: Flask):
    """Initialize the database with the application configuration."""
    app.config.from_object(Config)
    db.init_app(app)
    with app.app_context():
        db.create_all()  # Create tables if they don't exist
        logger.info("Database tables initialized.")

def populate_inventory(app):
    with app.app_context():
        products = []
        for i in range(1, 11):
            product = Product(
                id=f"prod_{i}",
                title=f"Product {i}"
            )
            variant = Variant(
                id=f"var_{i}",
                product_id=product.id,
                title=f"Variant {i}",
                inventory_item_id=f"inv_item_{i}"
            )
            inventory_item = InventoryItem(
                id=f"inv_item_{i}",
                variant_id=variant.id,
                tracked=True
            )
            inventory_level = InventoryLevel(
                inventory_item_id=inventory_item.id,
                available=randint(10, 100),
                updated_at=datetime.now()
            )
            products.append(product)
            db.session.add_all([product, variant, inventory_item, inventory_level])
        db.session.commit()

def populate_orders(app, num_orders=500, shop="quickstart-c21ead54.myshopify.com"):
    with app.app_context():
        products = Product.query.all()
        for i in range(num_orders):
            product = choice(products)
            order = Order(
                id=f"order_{i}",
                shop=shop,
                created_at=datetime.now() - timedelta(days=randint(0, 30))
            )
            line_item = LineItem(
                order_id=order.id,
                product_id=product.id,
                product_title=product.title,
                quantity=randint(1, 10)
            )
            db.session.add_all([order, line_item])
        db.session.commit()

def populate_mock_data(app, session_data=None):
    with app.app_context():
        order_count = Order.query.count()
        product_count = Product.query.count()
        if order_count == 0 or product_count == 0:
            app.logger.info("No orders or products found. Populating mock data...")
            try:
                populate_inventory(app)
                populate_orders(app, num_orders=500)
                app.logger.info("Mock data populated successfully.")
            except Exception as e:
                db.session.rollback()
                app.logger.error(f"Failed to populate mock data: {e}")


def clear_database(app: Flask):
    """Clear all data from the database (for testing or reset purposes)."""
    with app.app_context():
        try:
            db.session.query(InventoryLevel).delete()
            db.session.query(InventoryItem).delete()
            db.session.query(Variant).delete()
            db.session.query(Product).delete()
            db.session.query(LineItem).delete()
            db.session.query(Order).delete()
            db.session.commit()
            logger.info("Database cleared successfully.")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to clear database: {e}")

# Define PRODUCTS_DATA globally for use in populate_orders
PRODUCTS_DATA = [
    {"id": "8920988975395", "title": "T-Shirt"},
    {"id": "8922165477667", "title": "Hoodie"},
    {"id": "8920989204771", "title": "Mug"},
    {"id": "8920989106467", "title": "Hat"},
    {"id": "8920988877091", "title": "Backpack"},
    {"id": "8920988909859", "title": "Sneakers"},
    {"id": "8920989237539", "title": "Socks"},
    {"id": "8920989172003", "title": "Jacket"},
    {"id": "8920989073699", "title": "Scarf"},
    {"id": "8920988942627", "title": "Gloves"},
]