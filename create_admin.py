#!/usr/bin/env python3
"""
Script to create an admin user for FlashLog application.
Run this script once to set up the initial admin user.
"""

import sqlite3
import os
from werkzeug.security import generate_password_hash

def create_admin_user():
    """Create an admin user in the database"""
    
    # Database path
    db_path = 'flashlog/users.db'
    
    # Ensure the directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables if they don't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            role TEXT DEFAULT 'user'
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            session_token TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    
    # Check if admin user already exists
    cursor.execute('SELECT * FROM users WHERE username = ?', ('admin',))
    existing_admin = cursor.fetchone()
    
    if existing_admin:
        print("❌ Admin user already exists!")
        print(f"   Username: {existing_admin[1]}")
        print(f"   Email: {existing_admin[2]}")
        print(f"   Role: {existing_admin[7]}")
        return
    
    # Create admin user
    admin_username = 'admin'
    admin_email = 'admin@flashlog.com'
    admin_password = 'admin123'  # Change this in production!
    admin_password_hash = generate_password_hash(admin_password)
    
    try:
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, role) 
            VALUES (?, ?, ?, ?)
        ''', (admin_username, admin_email, admin_password_hash, 'admin'))
        
        conn.commit()
        print("✅ Admin user created successfully!")
        print(f"   Username: {admin_username}")
        print(f"   Email: {admin_email}")
        print(f"   Password: {admin_password}")
        print(f"   Role: admin")
        print("\n⚠️  IMPORTANT: Change the default password after first login!")
        
    except sqlite3.IntegrityError as e:
        print(f"❌ Error creating admin user: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        conn.close()

def create_test_user():
    """Create a test user for development"""
    
    db_path = 'flashlog/users.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if test user already exists
    cursor.execute('SELECT * FROM users WHERE username = ?', ('testuser',))
    existing_user = cursor.fetchone()
    
    if existing_user:
        print("❌ Test user already exists!")
        return
    
    # Create test user
    test_username = 'testuser'
    test_email = 'test@flashlog.com'
    test_password = 'test123'
    test_password_hash = generate_password_hash(test_password)
    
    try:
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, role) 
            VALUES (?, ?, ?, ?)
        ''', (test_username, test_email, test_password_hash, 'user'))
        
        conn.commit()
        print("✅ Test user created successfully!")
        print(f"   Username: {test_username}")
        print(f"   Email: {test_email}")
        print(f"   Password: {test_password}")
        print(f"   Role: user")
        
    except sqlite3.IntegrityError as e:
        print(f"❌ Error creating test user: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 FlashLog User Creation Script")
    print("=" * 40)
    
    # Create admin user
    print("\n1. Creating admin user...")
    create_admin_user()
    
    # Create test user
    print("\n2. Creating test user...")
    create_test_user()
    
    print("\n✅ Setup complete!")
    print("\n📋 Login Credentials:")
    print("   Admin: admin / admin123")
    print("   Test:  testuser / test123")
    print("\n🔐 Remember to change passwords after first login!") 