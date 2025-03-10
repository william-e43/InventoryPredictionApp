import sys
import os
import pytest
from datetime import datetime, timedelta

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

@pytest.fixture
def app():
    from app import create_app
    app = create_app()
    with app.app_context():
        from app.models import db, Order, LineItem, Product, Variant, InventoryItem, InventoryLevel

        # Clear existing data before adding mock data
        db.session.query(InventoryLevel).delete()
        db.session.query(InventoryItem).delete()
        db.session.query(Variant).delete()
        db.session.query(Product).delete()
        db.session.query(LineItem).delete()
        db.session.query(Order).delete()
        db.session.commit()

        db.create_all()
        # Add mock data with unique IDs
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        product = Product(id=f"prod_{timestamp}", title="T-Shirt")
        inventory_item = InventoryItem(id=f"inv_{timestamp}_1", variant_id=None, tracked=True)
        variant = Variant(
            id=f"var_{timestamp}_1",
            product_id=product.id,
            title="T-Shirt - Red",
            inventory_item_id=inventory_item.id
        )
        inventory_item.variant_id = variant.id
        inventory_level = InventoryLevel(inventory_item_id=inventory_item.id, available=5)
        order = Order(id=f"order_{timestamp}", created_at=(datetime.now() - timedelta(days=1)).isoformat() + "Z")
        line_item = LineItem(order_id=order.id, product_id=product.id, product_title="T-Shirt", quantity=2)
        db.session.add_all([product, inventory_item, variant, inventory_level, order, line_item])
        db.session.commit()
        yield app, product.id  # Yield app and product_id for tests
        db.drop_all()