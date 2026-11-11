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
);

INSERT OR REPLACE INTO orders VALUES
('ORD1001', 'CUST_01', 'imad',  'Shipped',    'TCS',             '9400111899223',   'Nov 12', 'Blue Cotton Shirt (M)', 'Nov 08'),
('ORD1002', 'CUST_02', 'uzair', 'Delivered',  'Leopard Courier', '449012849102',    'Nov 05', 'Running Shoes (10)',    'Nov 01'),
('ORD1003', 'CUST_03', 'sidra', 'Processing', 'TCS Express',     'PENDING',         'Nov 15', 'Wireless Earbuds',      'Yesterday'),
('ORD1004', 'CUST_04', 'waji',  'Delivered',  'Trax',            '1Z999AA10123456', 'Nov 04', 'Ceramic Dinner Set',    'Nov 01'),
('ORD1005', 'CUST_05', 'Awais', 'Delivered',  'M&P',             '9400111899999',   'Nov 02', 'Winter Beanie',         'Oct 28');