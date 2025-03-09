from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# Order Models
class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.String(50), primary_key=True)
    created_at = db.Column(db.String(50), nullable=False)

    line_items = db.relationship("LineItem", backref="order", lazy=True)

class LineItem(db.Model):
    __tablename__ = "line_items"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.String(50), db.ForeignKey("orders.id"), nullable=False)
    product_id = db.Column(db.String(50), nullable=False)
    product_title = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)


# Inventory Models
class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.String(50), primary_key=True)  # Shopify Product ID
    title = db.Column(db.String(100), nullable=False)

    variants = db.relationship("Variant", backref="product", lazy=True)

class Variant(db.Model):
    __tablename__ = "variants"

    id = db.Column(db.String(50), primary_key=True)  # Shopify Variant ID
    product_id = db.Column(db.String(50), db.ForeignKey("products.id"), nullable=False)
    title = db.Column(db.String(100), nullable=False)  # e.g., "Red, Large"
    sku = db.Column(db.String(50), nullable=True)  # Stock Keeping Unit
    inventory_item_id = db.Column(db.String(50), nullable=False, unique=True)

class InventoryItem(db.Model):
    __tablename__ = "inventory_items"

    id = db.Column(db.String(50), primary_key=True)  # Shopify Inventory Item ID
    variant_id = db.Column(db.String(50), db.ForeignKey("variants.id"), nullable=False)
    tracked = db.Column(db.Boolean, default=True)  # Whether inventory is tracked

class InventoryLevel(db.Model):
    __tablename__ = "inventory_levels"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    inventory_item_id = db.Column(db.String(50), db.ForeignKey("inventory_items.id"), nullable=False)
    location_id = db.Column(db.String(50), default="default_location_1")  # Mock single location
    available = db.Column(db.Integer, nullable=False, default=0)  # Current stock level
    updated_at = db.Column(db.String(50), nullable=False, default=lambda: datetime.now().isoformat() + "Z")