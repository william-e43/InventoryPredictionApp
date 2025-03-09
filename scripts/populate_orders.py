# scripts/populate_orders.py
import os
import sys
import random
from datetime import datetime, timedelta
from faker import Faker

# Add the project root to the sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.models import Order, LineItem, db
from app import create_app

# Initialize Faker for random dates
fake = Faker()

# Product data based on earlier debugging session
PRODUCTS = [
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

def generate_random_date(start_date: datetime, end_date: datetime) -> str:
    """Generate a random date between start_date and end_date in ISO format."""
    time_delta = end_date - start_date
    random_days = random.randint(0, time_delta.days)
    random_date = start_date + timedelta(days=random_days)
    return random_date.isoformat() + "Z"

def populate_orders(num_orders: int = 500):
    """Generate and insert mock orders into the database."""
    app = create_app()
    with app.app_context():
        # Clear existing data (optional, comment out if you want to append)
        db.session.query(LineItem).delete()
        db.session.query(Order).delete()
        db.session.commit()

        # Define date range: last 3 months (Dec 9, 2024 to Mar 9, 2025)
        end_date = datetime(2025, 3, 9)
        start_date = end_date - timedelta(days=90)  # Approximately 3 months

        # Generate orders
        for i in range(num_orders):
            order_id = f"mock_order_{i+1}"
            created_at = generate_random_date(start_date, end_date)

            # Create order
            order = Order(id=order_id, created_at=created_at)

            # Generate 1 to 5 line items per order
            num_line_items = random.randint(1, 5)
            selected_products = random.sample(PRODUCTS, k=num_line_items)

            for product in selected_products:
                quantity = random.randint(1, 10)  # Random quantity between 1 and 10
                line_item = LineItem(
                    order_id=order_id,
                    product_id=product["id"],
                    product_title=product["title"],
                    quantity=quantity,
                )
                order.line_items.append(line_item)

            db.session.add(order)

        # Commit all changes
        db.session.commit()
        print(f"Successfully populated {num_orders} mock orders.")

if __name__ == "__main__":
    populate_orders()