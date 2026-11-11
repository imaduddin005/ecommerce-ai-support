import sqlite3
import os

DB_PATH = "orders.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL,
            customer_name TEXT NOT NULL,
            status TEXT NOT NULL,
            carrier TEXT NOT NULL,
            tracking_number TEXT NOT NULL,
            estimated_delivery TEXT NOT NULL,
            items TEXT NOT NULL,
            order_date TEXT NOT NULL
        )
    """)
    cursor.execute("DELETE FROM orders")
    
    # 5 distinct customers or consistent accounts
    sample_orders = [
        ('ORD1001', 'CUST_01', 'imad',  'Shipped',    'TCS',             '9400111899223',   'Nov 12', 'Blue Cotton Shirt (M)', 'Nov 08'),
        ('ORD1002', 'CUST_02', 'uzair', 'Delivered',  'Leopard Courier', '449012849102',    'Nov 05', 'Running Shoes (10)',    'Nov 01'),
        ('ORD1003', 'CUST_01', 'imad',  'Processing', 'TCS Express',     'PENDING',         'Nov 15', 'Wireless Earbuds',      'Yesterday'),
        ('ORD1004', 'CUST_03', 'waji',  'Delivered',  'Trax',            '1Z999AA10123456', 'Nov 04', 'Ceramic Dinner Set',    'Nov 01'),
        ('ORD1005', 'CUST_01', 'imad',  'Delivered',  'M&P',             '9400111899999',   'Nov 02', 'Winter Beanie',         'Oct 28')
    ]
    cursor.executemany("""
        INSERT INTO orders (order_id, customer_id, customer_name, status, carrier, tracking_number, estimated_delivery, items, order_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, sample_orders)
    conn.commit()
    conn.close()
    print("Database orders.db initialized successfully.")

def query_order_secure(order_id: str, authenticated_customer_id: str) -> dict:
    if not os.path.exists(DB_PATH):
        init_db()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT customer_id, customer_name, status, items, carrier, tracking_number, estimated_delivery FROM orders WHERE UPPER(order_id) = UPPER(?)",
        (order_id.strip(),)
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        return {
            "status": "error",
            "message": f"Your order ID '{order_id.upper()}' is wrong or does not exist in our system. Please verify your order number and try again."
        }

    cust_id, cust_name, status_val, items, carrier, tracking_number, estimated_delivery = row

    if cust_id.upper() != authenticated_customer_id.upper():
        return {
            "status": "denied",
            "message": "Access Denied: You are not authorized to view details for this order. Please log in with the correct account."
        }

    return {
        "status": "success",
        "order_id": order_id.upper(),
        "customer_name": cust_name,
        "order_status": status_val,
        "items": items,
        "carrier": carrier,
        "tracking_number": tracking_number,
        "estimated_delivery": estimated_delivery
    }

def get_latest_order_for_customer(customer_id: str) -> dict:
    if not os.path.exists(DB_PATH):
        init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT order_id, customer_name, status, items, carrier, tracking_number, estimated_delivery FROM orders WHERE customer_id = ? ORDER BY order_id DESC LIMIT 1",
        (customer_id.strip(),)
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        return {"status": "error", "message": "No recent orders found on your account."}
    return {
        "status": "success",
        "order_id": row[0],
        "customer_name": row[1],
        "order_status": row[2],
        "items": row[3],
        "carrier": row[4],
        "tracking_number": row[5],
        "estimated_delivery": row[6]
    }