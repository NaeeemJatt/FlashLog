#!/usr/bin/env python3
"""
Database Migration Script for FlashLog
Adds new columns to user_activities table for enhanced activity tracking
"""

import sqlite3
import os
import sys

def migrate_database():
    """Migrate the database to add new columns to user_activities table"""
    
    db_path = 'flashlog/users.db'
    
    # Check if database exists
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        print("Creating new database with updated schema...")
        return
    
    print(f"🔍 Found database at {db_path}")
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get current table schema
        cursor.execute("PRAGMA table_info(user_activities)")
        columns = [column[1] for column in cursor.fetchall()]
        
        print(f"📋 Current columns in user_activities: {columns}")
        
        # Define new columns to add
        new_columns = [
            ('status', 'TEXT DEFAULT "success"'),
            ('ip_address', 'TEXT'),
            ('user_agent', 'TEXT'),
            ('old_value', 'TEXT'),
            ('new_value', 'TEXT')
        ]
        
        # Add missing columns
        added_columns = []
        for column_name, column_def in new_columns:
            if column_name not in columns:
                try:
                    sql = f"ALTER TABLE user_activities ADD COLUMN {column_name} {column_def}"
                    cursor.execute(sql)
                    added_columns.append(column_name)
                    print(f"✅ Added column: {column_name}")
                except sqlite3.OperationalError as e:
                    print(f"⚠️  Column {column_name} might already exist: {e}")
            else:
                print(f"ℹ️  Column {column_name} already exists")
        
        # Commit changes
        conn.commit()
        
        # Verify the migration
        cursor.execute("PRAGMA table_info(user_activities)")
        final_columns = [column[1] for column in cursor.fetchall()]
        print(f"📋 Final columns in user_activities: {final_columns}")
        
        # Check if all required columns are present
        required_columns = [
            'id', 'user_id', 'activity_type', 'description', 'details',
            'status', 'ip_address', 'user_agent', 'file_name', 'file_size',
            'processing_time', 'anomalies_detected', 'total_logs',
            'old_value', 'new_value', 'created_at'
        ]
        
        missing_columns = [col for col in required_columns if col not in final_columns]
        
        if missing_columns:
            print(f"❌ Missing required columns: {missing_columns}")
            return False
        else:
            print("✅ All required columns are present!")
        
        # Get activity count
        cursor.execute("SELECT COUNT(*) FROM user_activities")
        activity_count = cursor.fetchone()[0]
        print(f"📊 Total activities in database: {activity_count}")
        
        conn.close()
        
        if added_columns:
            print(f"\n🎉 Migration completed successfully!")
            print(f"Added columns: {added_columns}")
        else:
            print(f"\n✅ Database is already up to date!")
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def backup_database():
    """Create a backup of the database before migration"""
    import shutil
    from datetime import datetime
    
    db_path = 'flashlog/users.db'
    if not os.path.exists(db_path):
        print("No database to backup")
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f'flashlog/users_backup_{timestamp}.db'
    
    try:
        shutil.copy2(db_path, backup_path)
        print(f"💾 Database backed up to: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return None

if __name__ == "__main__":
    print("🚀 FlashLog Database Migration Tool")
    print("=" * 50)
    
    # Create backup
    backup_path = backup_database()
    
    # Run migration
    success = migrate_database()
    
    if success:
        print("\n✅ Migration completed successfully!")
        print("You can now restart your Flask application.")
        if backup_path:
            print(f"Backup saved at: {backup_path}")
    else:
        print("\n❌ Migration failed!")
        if backup_path:
            print(f"Your original database is backed up at: {backup_path}")
        sys.exit(1) 