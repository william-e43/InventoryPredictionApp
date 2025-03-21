from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# Order Models
class Order(db.Model):
    __tablename__ = "orders"
    id = db.Column(db.String(50), primary_key=True)
    shop = db.Column(db.String(255), nullable=False)  # Add shop column
    created_at = db.Column(db.DateTime, nullable=False)  # Change to DateTime
    line_items = db.relationship("LineItem", backref="order", lazy=True)

class LineItem(db.Model):
    __tablename__ = "line_items"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.String(50), db.ForeignKey("orders.id"), nullable=False)
    product_id = db.Column(db.String(50), nullable=False)
    product_title = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    # Add a relationship to Product for easier querying
    product = db.relationship("Product", primaryjoin="LineItem.product_id == Product.id", foreign_keys="LineItem.product_id", backref="line_items")

# Inventory Models
class Product(db.Model):
    __tablename__ = "products"
    id = db.Column(db.String(50), primary_key=True)  # Shopify Product ID
    title = db.Column(db.String(100), nullable=False)
    variants = db.relationship("Variant", backref="product", lazy=True)

    @property
    def total_stock(self):
        """
        Calculate the total stock for this product by summing InventoryLevel.available across all variants.
        """
        stock = 0
        for variant in self.variants:
            for inventory_level in variant.inventory_levels:
                stock += inventory_level.available
        return stock

class Variant(db.Model):
    __tablename__ = "variants"
    id = db.Column(db.String(50), primary_key=True)  # Shopify Variant ID
    product_id = db.Column(db.String(50), db.ForeignKey("products.id"), nullable=False)
    title = db.Column(db.String(100), nullable=False)  # e.g., "Red, Large"
    sku = db.Column(db.String(50), nullable=True)  # Stock Keeping Unit
    inventory_item_id = db.Column(db.String(50), nullable=False, unique=True)
    inventory_items = db.relationship("InventoryItem", backref="variant", lazy=True)

    @property
    def inventory_levels(self):
        """
        Get all inventory levels for this variant.
        """
        return [item.inventory_level for item in self.inventory_items if item.inventory_level]

class InventoryItem(db.Model):
    __tablename__ = "inventory_items"
    id = db.Column(db.String(50), primary_key=True)  # Shopify Inventory Item ID
    variant_id = db.Column(db.String(50), db.ForeignKey("variants.id"), nullable=False)
    tracked = db.Column(db.Boolean, default=True)  # Whether inventory is tracked
    inventory_level = db.relationship("InventoryLevel", backref="inventory_item", uselist=False, lazy=True)

class InventoryLevel(db.Model):
    __tablename__ = "inventory_levels"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    inventory_item_id = db.Column(db.String(50), db.ForeignKey("inventory_items.id"), nullable=False)
    location_id = db.Column(db.String(50), default="default_location_1")  # Mock single location
    available = db.Column(db.Integer, nullable=False, default=0)  # Current stock level
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now)  # Change to DateTime