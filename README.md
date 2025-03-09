# Inventory Prediction App

A Flask-based inventory management tool integrated with Shopify, using SQLite for mock data.

## Setup
1. Clone the repository: `git clone https://github.com/<your-username>/InventoryPredictionApp.git`
2. Create a virtual environment: `python -m venv .venv`
3. Activate the virtual environment: `source .venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Run the app: `python run.py`
6. Start ngrok: `ngrok http 5000`

## Mock Data
- Populated via `scripts/populate_orders.py` (500 orders) and `app/database.py` (inventory).
- Clear data: `from app.database import clear_database; clear_database(create_app())`

## Features
- Displays daily sales, top products, and inventory levels.
- Includes low stock alerts and stock depletion predictions.