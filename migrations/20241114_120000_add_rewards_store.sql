-- Name: Add Rewards Store System
-- Description: Add complete rewards store with products, orders, cart, and wishlist
-- Version: 20241114_120000
-- Created: 2024-11-14T12:00:00

-- Products table
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL,
    points_required INTEGER NOT NULL,
    original_price DECIMAL(10,2),
    stock_quantity INTEGER DEFAULT 0 NOT NULL,
    max_quantity_per_user INTEGER DEFAULT 1 NOT NULL,
    status VARCHAR(20) DEFAULT 'ACTIVE' NOT NULL,
    image_url VARCHAR(500),
    brand VARCHAR(100),
    specifications JSON,
    college_id INTEGER NOT NULL REFERENCES colleges(id),
    created_by INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Orders table
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    order_number VARCHAR(50) UNIQUE NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id),
    total_points INTEGER NOT NULL,
    total_items INTEGER NOT NULL,
    status VARCHAR(30) DEFAULT 'PENDING' NOT NULL,
    notes TEXT,
    pickup_location VARCHAR(255),
    estimated_pickup_date TIMESTAMP,
    college_id INTEGER NOT NULL REFERENCES colleges(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Order Items table
CREATE TABLE IF NOT EXISTS order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id),
    quantity INTEGER NOT NULL,
    points_per_item INTEGER NOT NULL,
    total_points INTEGER NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Carts table
CREATE TABLE IF NOT EXISTS carts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    college_id INTEGER NOT NULL REFERENCES colleges(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Cart Items table
CREATE TABLE IF NOT EXISTS cart_items (
    id SERIAL PRIMARY KEY,
    cart_id INTEGER NOT NULL REFERENCES carts(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id),
    quantity INTEGER NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Point Transactions table
CREATE TABLE IF NOT EXISTS point_transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    transaction_type VARCHAR(50) NOT NULL,
    points INTEGER NOT NULL,
    balance_after INTEGER NOT NULL,
    description VARCHAR(500) NOT NULL,
    reference_type VARCHAR(50),
    reference_id INTEGER,
    college_id INTEGER NOT NULL REFERENCES colleges(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Wishlist Items table
CREATE TABLE IF NOT EXISTS wishlist_items (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    product_id INTEGER NOT NULL REFERENCES products(id),
    college_id INTEGER NOT NULL REFERENCES colleges(id),
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, product_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_products_college_category ON products(college_id, category);
CREATE INDEX IF NOT EXISTS idx_orders_user_created ON orders(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_point_transactions_user_created ON point_transactions(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_cart_items_cart ON cart_items(cart_id);
CREATE INDEX IF NOT EXISTS idx_wishlist_user_product ON wishlist_items(user_id, product_id);

-- Add sample products for existing colleges (only if no products exist yet)
INSERT INTO products (name, description, category, points_required, original_price, 
                    stock_quantity, max_quantity_per_user, status, brand, college_id, created_by)
SELECT 
    'Wireless Bluetooth Headphones' as name,
    'High-quality wireless headphones with noise cancellation' as description,
    'ELECTRONICS'::ProductCategory as category,
    500 as points_required,
    2500.00 as original_price,
    10 as stock_quantity,
    1 as max_quantity_per_user,
    'ACTIVE'::ProductStatus as status,
    'TechBrand' as brand,
    c.id as college_id,
    u.id as created_by
FROM colleges c 
JOIN LATERAL (
    SELECT id FROM users WHERE college_id = c.id LIMIT 1
) u ON true
WHERE NOT EXISTS (SELECT 1 FROM products WHERE college_id = c.id);

-- Add more sample products for each college (only if the first product was successfully added)
INSERT INTO products (name, description, category, points_required, original_price, 
                    stock_quantity, max_quantity_per_user, status, brand, college_id, created_by)
SELECT 
    product_data.name,
    product_data.description,
    product_data.category::ProductCategory,
    product_data.points_required,
    product_data.original_price,
    product_data.stock_quantity,
    product_data.max_quantity_per_user,
    product_data.status::ProductStatus,
    product_data.brand,
    c.id as college_id,
    u.id as created_by
FROM colleges c 
JOIN LATERAL (
    SELECT id FROM users WHERE college_id = c.id LIMIT 1
) u ON true
CROSS JOIN (
    VALUES 
    ('USB Power Bank 10000mAh', 'Portable power bank for charging devices', 'ELECTRONICS', 300, 1500.00, 20, 1, 'ACTIVE', 'PowerMax'),
    ('Data Structures Book', 'Comprehensive DSA guide', 'BOOKS', 400, 2000.00, 8, 1, 'ACTIVE', 'TechBooks'),
    ('Premium Notebook Set', 'Set of 3 high-quality notebooks', 'STATIONERY', 150, 750.00, 25, 2, 'ACTIVE', 'WriteWell'),
    ('Campus Cafeteria Voucher ₹100', 'Food voucher for campus cafeteria', 'FOOD_VOUCHERS', 80, 100.00, 50, 5, 'ACTIVE', 'Campus Cafe'),
    ('Amazon Gift Card ₹500', 'Amazon shopping gift card', 'GIFT_CARDS', 400, 500.00, 20, 1, 'ACTIVE', 'Amazon'),
    ('Spotify Premium 1 Month', 'Music streaming subscription', 'SOFTWARE', 120, 149.00, 100, 1, 'ACTIVE', 'Spotify')
) AS product_data(name, description, category, points_required, original_price, stock_quantity, max_quantity_per_user, status, brand)
WHERE EXISTS (SELECT 1 FROM products WHERE college_id = c.id AND name = 'Wireless Bluetooth Headphones') -- Only add if college has the first sample product
AND NOT EXISTS (
    SELECT 1 FROM products p2 
    WHERE p2.college_id = c.id AND p2.name = product_data.name
);