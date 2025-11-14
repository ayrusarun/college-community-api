#!/usr/bin/env python3

"""
Store Migration Script - Add Rewards Store Tables
Run this script to add store tables and sample products to existing database.

Usage:
    python migrate_store.py

Features:
- Checks if tables already exist (safe to run multiple times)
- Creates tables only if they don't exist
- Adds sample products only if none exist
- Works with existing database from init_db.py
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

# Database configuration
DATABASE_URL = os.getenv(
    'DATABASE_URL', 
    'postgresql://college_user:college_pass@localhost:5432/college_community_db'
)

def check_table_exists(engine, table_name):
    """Check if table exists in database"""
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = :table_name)"
        ), {"table_name": table_name})
        return result.scalar()

def run_migration():
    """Run the store migration"""
    print("🏪 College Community Store Migration")
    print("=" * 40)
    
    try:
        # Connect to database
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        print(f"📡 Connecting to database...")
        
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Database connection successful")
        
        # Check existing tables
        tables_to_create = [
            'products', 'orders', 'order_items', 'carts', 
            'cart_items', 'point_transactions', 'wishlist_items'
        ]
        
        existing_tables = []
        missing_tables = []
        
        for table in tables_to_create:
            if check_table_exists(engine, table):
                existing_tables.append(table)
            else:
                missing_tables.append(table)
        
        if existing_tables:
            print(f"⏭️  Found existing tables: {', '.join(existing_tables)}")
        
        if not missing_tables:
            print("✅ All store tables already exist!")
        else:
            print(f"🔨 Creating missing tables: {', '.join(missing_tables)}")
            
            # Create tables SQL
            create_sql = """
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

            CREATE TABLE IF NOT EXISTS carts (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                college_id INTEGER NOT NULL REFERENCES colleges(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS cart_items (
                id SERIAL PRIMARY KEY,
                cart_id INTEGER NOT NULL REFERENCES carts(id) ON DELETE CASCADE,
                product_id INTEGER NOT NULL REFERENCES products(id),
                quantity INTEGER NOT NULL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

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

            CREATE TABLE IF NOT EXISTS wishlist_items (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                product_id INTEGER NOT NULL REFERENCES products(id),
                college_id INTEGER NOT NULL REFERENCES colleges(id),
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, product_id)
            );

            -- Create indexes
            CREATE INDEX IF NOT EXISTS idx_products_college_category ON products(college_id, category);
            CREATE INDEX IF NOT EXISTS idx_orders_user_created ON orders(user_id, created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_point_transactions_user_created ON point_transactions(user_id, created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_cart_items_cart ON cart_items(cart_id);
            """
            
            with engine.connect() as conn:
                conn.execute(text(create_sql))
                conn.commit()
            
            print("✅ Store tables created successfully")
        
        # Check and add sample products
        db = SessionLocal()
        try:
            product_count = db.execute(text("SELECT COUNT(*) FROM products")).scalar()
            
            if product_count == 0:
                print("📦 Adding sample products...")
                
                # Get all colleges for sample data
                colleges = db.execute(text("SELECT id, name FROM colleges")).fetchall()
                products_added = 0
                
                for college_id, college_name in colleges:
                    # Get first user from college as creator
                    creator = db.execute(
                        text("SELECT id FROM users WHERE college_id = :college_id LIMIT 1"),
                        {"college_id": college_id}
                    ).fetchone()
                    
                    if creator:
                        creator_id = creator[0]
                        
                        sample_products = """
                        INSERT INTO products (name, description, category, points_required, original_price, 
                                            stock_quantity, max_quantity_per_user, status, brand, college_id, created_by) 
                        VALUES 
                        ('Wireless Bluetooth Headphones', 'High-quality wireless headphones with noise cancellation', 'ELECTRONICS', 500, 2500.00, 10, 1, 'ACTIVE', 'TechBrand', :college_id, :creator_id),
                        ('USB Power Bank 10000mAh', 'Portable power bank for charging devices', 'ELECTRONICS', 300, 1500.00, 20, 1, 'ACTIVE', 'PowerMax', :college_id, :creator_id),
                        ('Data Structures Book', 'Comprehensive DSA guide', 'BOOKS', 400, 2000.00, 8, 1, 'ACTIVE', 'TechBooks', :college_id, :creator_id),
                        ('Premium Notebook Set', 'Set of 3 high-quality notebooks', 'STATIONERY', 150, 750.00, 25, 2, 'ACTIVE', 'WriteWell', :college_id, :creator_id),
                        ('Campus Cafeteria Voucher ₹100', 'Food voucher for campus cafeteria', 'FOOD_VOUCHERS', 80, 100.00, 50, 5, 'ACTIVE', 'Campus Cafe', :college_id, :creator_id),
                        ('Amazon Gift Card ₹500', 'Amazon shopping gift card', 'GIFT_CARDS', 400, 500.00, 20, 1, 'ACTIVE', 'Amazon', :college_id, :creator_id),
                        ('Spotify Premium 1 Month', 'Music streaming subscription', 'SOFTWARE', 120, 149.00, 100, 1, 'ACTIVE', 'Spotify', :college_id, :creator_id);
                        """
                        
                        db.execute(text(sample_products), {
                            "college_id": college_id,
                            "creator_id": creator_id
                        })
                        products_added += 7
                        print(f"   ✅ Added 7 products for {college_name}")
                
                db.commit()
                print(f"✅ Total {products_added} sample products added")
            else:
                print(f"⏭️  Products already exist ({product_count} found), skipping sample data")
        
        finally:
            db.close()
        
        # Final summary
        print("\n🎉 Migration completed successfully!")
        db = SessionLocal()
        try:
            total_products = db.execute(text("SELECT COUNT(*) FROM products")).scalar()
            total_colleges = db.execute(text("SELECT COUNT(*) FROM colleges")).scalar()
            print(f"📊 Final status: {total_products} products across {total_colleges} colleges")
        finally:
            db.close()
            
    except SQLAlchemyError as e:
        print(f"❌ Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_migration()