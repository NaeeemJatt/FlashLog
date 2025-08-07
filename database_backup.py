#!/usr/bin/env python3
"""
Database Backup Utility for FlashLog Learning System
Manages backup and restore operations between main and backup databases
"""

import sqlite3
import shutil
import os
from datetime import datetime
import json

class DatabaseBackupManager:
    def __init__(self):
        self.main_db = 'flashlog.db'
        self.backup_db = 'flashlog/flashlog.db'
        
    def create_backup(self):
        """Create a backup of the main database"""
        try:
            if not os.path.exists(self.main_db):
                print(f"❌ Main database {self.main_db} not found!")
                return False
                
            # Create backup directory if it doesn't exist
            os.makedirs('flashlog', exist_ok=True)
            
            # Copy main database to backup location
            shutil.copy2(self.main_db, self.backup_db)
            
            print(f"✅ Backup created successfully!")
            print(f"   Main: {self.main_db}")
            print(f"   Backup: {self.backup_db}")
            return True
            
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            return False
    
    def restore_from_backup(self):
        """Restore main database from backup"""
        try:
            if not os.path.exists(self.backup_db):
                print(f"❌ Backup database {self.backup_db} not found!")
                return False
                
            # Create backup of current main database before restoring
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            current_backup = f"flashlog.db.backup_{timestamp}"
            
            if os.path.exists(self.main_db):
                shutil.copy2(self.main_db, current_backup)
                print(f"📦 Current main database backed up as {current_backup}")
            
            # Restore from backup
            shutil.copy2(self.backup_db, self.main_db)
            
            print(f"✅ Database restored successfully from backup!")
            print(f"   Restored: {self.main_db}")
            print(f"   From: {self.backup_db}")
            return True
            
        except Exception as e:
            print(f"❌ Restore failed: {e}")
            return False
    
    def compare_databases(self):
        """Compare main and backup databases"""
        try:
            main_conn = sqlite3.connect(self.main_db)
            backup_conn = sqlite3.connect(self.backup_db)
            
            main_cursor = main_conn.cursor()
            backup_cursor = backup_conn.cursor()
            
            print("📊 Database Comparison:")
            print("=" * 50)
            
            # Compare table counts
            tables = ['algorithm_learnings', 'learning_sessions', 'learned_patterns', 'learning_metrics', 'learning_impact_tracking']
            
            for table in tables:
                try:
                    main_count = main_cursor.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
                    backup_count = backup_cursor.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
                    
                    status = "✅" if main_count == backup_count else "❌"
                    print(f"{status} {table}: Main={main_count}, Backup={backup_count}")
                    
                except sqlite3.OperationalError:
                    print(f"⚠️  {table}: Table not found in one or both databases")
            
            # Show learning status distribution
            try:
                main_status = main_cursor.execute('''
                    SELECT status, COUNT(*) FROM algorithm_learnings 
                    GROUP BY status
                ''').fetchall()
                
                backup_status = backup_cursor.execute('''
                    SELECT status, COUNT(*) FROM algorithm_learnings 
                    GROUP BY status
                ''').fetchall()
                
                print(f"\n📈 Learning Status Distribution:")
                print(f"Main DB: {dict(main_status)}")
                print(f"Backup DB: {dict(backup_status)}")
                
            except sqlite3.OperationalError:
                print("⚠️  Could not compare learning status")
            
            main_conn.close()
            backup_conn.close()
            
        except Exception as e:
            print(f"❌ Comparison failed: {e}")
    
    def get_database_info(self):
        """Get information about both databases"""
        print("📋 Database Information:")
        print("=" * 50)
        
        for db_name, db_path in [("Main", self.main_db), ("Backup", self.backup_db)]:
            if os.path.exists(db_path):
                size = os.path.getsize(db_path)
                modified = datetime.fromtimestamp(os.path.getmtime(db_path))
                print(f"{db_name} Database:")
                print(f"  Path: {db_path}")
                print(f"  Size: {size:,} bytes")
                print(f"  Modified: {modified}")
                
                # Get table info
                try:
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = cursor.fetchall()
                    print(f"  Tables: {len(tables)}")
                    conn.close()
                except:
                    print(f"  Tables: Unable to read")
                print()
            else:
                print(f"{db_name} Database: Not found")
                print()

def main():
    """Main backup utility interface"""
    manager = DatabaseBackupManager()
    
    print("🔄 FlashLog Database Backup Utility")
    print("=" * 50)
    
    while True:
        print("\nOptions:")
        print("1. Create backup")
        print("2. Restore from backup")
        print("3. Compare databases")
        print("4. Show database info")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == '1':
            manager.create_backup()
        elif choice == '2':
            confirm = input("⚠️  This will overwrite the main database. Continue? (y/N): ")
            if confirm.lower() == 'y':
                manager.restore_from_backup()
            else:
                print("❌ Restore cancelled")
        elif choice == '3':
            manager.compare_databases()
        elif choice == '4':
            manager.get_database_info()
        elif choice == '5':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
