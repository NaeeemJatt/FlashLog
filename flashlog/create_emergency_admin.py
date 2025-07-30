#!/usr/bin/env python3
"""
Emergency Admin User Creation Script
This script creates an emergency admin user with username 'jatt' and password 'jatt'
Use this script only when no admin users are available in the system.
"""

import sqlite3
import os
from werkzeug.security import generate_password_hash
from datetime import datetime
import getpass

def create_emergency_admin():
    """Create emergency admin user with username 'jatt' and password 'jatt'"""
    
    db_path = 'flashlog/users.db'
    
    # Check if database exists
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        print("Please run the application first to initialize the database.")
        return False
    
    print(f"🔍 Creating emergency admin user in {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if admin user 'jatt' already exists
        cursor.execute('SELECT * FROM users WHERE username = ?', ('jatt',))
        existing_admin = cursor.fetchone()
        
        if existing_admin:
            print("❌ Admin user 'jatt' already exists!")
            print("If you need to reset the password, please use the admin panel or delete the user first.")
            return False
        
        # Prompt for credentials securely
        admin_username = input('Enter admin username: ').strip()
        admin_email = input('Enter admin email: ').strip()
        admin_password = getpass.getpass('Enter admin password: ')
        confirm_password = getpass.getpass('Confirm admin password: ')
        
        if not admin_username or not admin_email or not admin_password:
            print('❌ All fields are required!')
            return
        
        if admin_password != confirm_password:
            print('❌ Passwords do not match!')
            return
        
        # Validate password strength (add basic checks)
        if len(admin_password) < 12:
            print('❌ Password must be at least 12 characters long!')
            return
        
        admin_password_hash = generate_password_hash(admin_password)
        
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, role, created_at) 
            VALUES (?, ?, ?, ?, ?)
        ''', (admin_username, admin_email, admin_password_hash, 'admin', datetime.now()))
        
        conn.commit()
        conn.close()
        
        print(f'✅ Emergency admin user created successfully!')
        print(f'Username: {admin_username}')
        print(f'Email: {admin_email}')
        print('⚠️ Password is not displayed for security. Remember it securely.')
        
        return True
        
    except sqlite3.IntegrityError as e:
        print(f"❌ Database integrity error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Main function to run the script"""
    print("🚨 Emergency Admin User Creation Script")
    print("=" * 50)
    print("This script creates an emergency admin user with:")
    print("Username: jatt")
    print("Password: jatt")
    print("Role: admin")
    print("\n⚠️  WARNING: This creates a user with a weak password!")
    print("Only use this script when no admin users are available.")
    print("=" * 50)
    
    # Ask for confirmation
    response = input("\nDo you want to proceed? (yes/no): ").lower().strip()
    
    if response in ['yes', 'y']:
        success = create_emergency_admin()
        if success:
            print("\n🎉 Emergency admin user created successfully!")
            print("You can now log in to the system.")
        else:
            print("\n❌ Failed to create emergency admin user.")
    else:
        print("\n❌ Operation cancelled.")

if __name__ == "__main__":
    main() 