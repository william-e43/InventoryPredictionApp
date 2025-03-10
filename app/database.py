# app/database.py
import logging
import random
from flask import Flask
from .models import db, Order, LineItem, Product, Variant, InventoryItem, InventoryLevel
from .config import Config
from datetime import datetime, timedelta
import os

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

def populate_orders(app: Flask, num_orders=500):
    """Populate the database with a specified number of mock orders."""
    with app.app_context():
        PRODUCTS = [
            "8920988975395", "8922165477667", "8920989204771", "8920989106467",
            "8920988877091", "8920988909859", "8920989237539", "8920989172003",
            "8920989073699", "8920988942627"
        ]
        for i in range(num_orders):
            order_id = f"mock_order_{i+1}"
            created_at = (datetime.now() - timedelta(days=random.randint(1, 60))).isoformat() + "Z"
            order = Order(id=order_id, created_at=created_at)
            num_line_items = random.randint(1, 5)
            selected_products = random.sample(PRODUCTS, k=num_line_items)
            for product_id in selected_products:
                quantity = random.randint(1, 5)
                line_item = LineItem(
                    order_id=order_id,
                    product_id=product_id,
                    product_title=next(p["title"] for p in PRODUCTS_DATA if p["id"] == product_id),
                    quantity=quantity
                )
                order.line_items.append(line_item)
            db.session.add(order)
        db.session.commit()
        logger.info(f"Populated {num_orders} mock orders successfully.")

def populate_inventory(app: Flask):
    """Populate the database with mock inventory data."""
    with app.app_context():
        variants_data = []
        for product in PRODUCTS_DATA:
            num_variants = random.randint(1, 4)
            for i in range(1, num_variants + 1):
                variant_id = f"var_{product['id']}_{i}"
                variants_data.append({
                    "id": variant_id,
                    "product_id": product["id"],
                    "title": f"{product['title']} - {random.choice(['Small', 'Medium', 'Large', 'Red', 'Blue'])}",
                    "sku": f"SKU-{variant_id}",
                    "inventory_item_id": f"inv_{variant_id}",
                })

        # Insert products
        for product_data in PRODUCTS_DATA:
            product = Product(id=product_data["id"], title=product_data["title"])
            db.session.add(product)

        # Insert variants and inventory items
        for variant_data in variants_data:
            variant = Variant(
                id=variant_data["id"],
                product_id=variant_data["product_id"],
                title=variant_data["title"],
                sku=variant_data["sku"],
                inventory_item_id=variant_data["inventory_item_id"],
            )
            inventory_item = InventoryItem(
                id=variant_data["inventory_item_id"],
                variant_id=variant_data["id"],
                tracked=True,
            )
            db.session.add(variant)
            db.session.add(inventory_item)

        # Insert inventory levels
        for variant_data in variants_data:
            inventory_level = InventoryLevel(
                inventory_item_id=variant_data["inventory_item_id"],
                available=random.randint(0, 100),
            )
            db.session.add(inventory_level)

        db.session.commit()
        logger.info("Populated mock inventory data successfully.")

def populate_mock_data(app: Flask, session_data: dict = None):
    """Populate the database with mock data if it’s empty."""
    with app.app_context():
        # Check if data already exists by counting orders
        order_count = Order.query.count()
        product_count = Product.query.count()
        if order_count == 0 or product_count == 0:
            logger.info("No orders or products found. Populating mock data...")
            try:
                # Populate inventory first (products, variants, inventory items, levels)
                populate_inventory(app)
                # Populate 500 orders
                populate_orders(app, num_orders=500)
                logger.info("Mock data (inventory and 500 orders) populated successfully.")
            except Exception as e:
                db.session.rollback()
                logger.error(f"Failed to populate mock data: {e}")
        else:
            logger.info(f"Database contains {order_count} orders and {product_count} products. Skipping default population.")

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