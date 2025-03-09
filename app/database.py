# app/database.py
import logging
import random
from flask import Flask
from .models import db, Order, LineItem, Product, Variant, InventoryItem, InventoryLevel
from .config import Config
from datetime import datetime


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

def populate_mock_data(app: Flask):
    """Populate the database with mock data if it’s empty."""
    with app.app_context():
        # Check if data already exists by counting orders
        order_count = Order.query.count()
        product_count = Product.query.count()
        if order_count == 0 or product_count == 0:
            logger.info("No orders or products found. Populating mock data...")
            try:
                # Populate products and variants
                products_data = [
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

                variants_data = []
                for product in products_data:
                    for i in range(1, random.randint(2, 4)):  # 2-4 variants per product
                        variant_id = f"var_{product['id']}_{i}"
                        variants_data.append({
                            "id": variant_id,
                            "product_id": product["id"],
                            "title": f"{product['title']} - {random.choice(['Small', 'Medium', 'Large', 'Red', 'Blue'])}",
                            "sku": f"SKU-{variant_id}",
                            "inventory_item_id": f"inv_{variant_id}",
                        })

                # Insert products
                for product_data in products_data:
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
                        available=random.randint(0, 100),  # Random stock level 0-100
                    )
                    db.session.add(inventory_level)

                # Minimal default order data as a fallback
                orders_data = [
                    {
                        "id": "default_mock_1",
                        "created_at": datetime.utcnow().isoformat() + "Z",
                        "line_items": [
                            {"product_id": "8920988975395", "product_title": "T-Shirt", "quantity": 1},
                        ],
                    },
                ]

                for order_data in orders_data:
                    order = Order(id=order_data["id"], created_at=order_data["created_at"])
                    for item_data in order_data["line_items"]:
                        line_item = LineItem(
                            order_id=order_data["id"],
                            product_id=item_data["product_id"],
                            product_title=item_data["product_title"],
                            quantity=item_data["quantity"],
                        )
                        order.line_items.append(line_item)
                    db.session.add(order)

                db.session.commit()
                logger.info("Mock inventory and default order data populated successfully.")
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