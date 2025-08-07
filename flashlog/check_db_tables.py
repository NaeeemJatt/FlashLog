import sqlite3

def check_database():
    try:
        conn = sqlite3.connect('flashlog.db')
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print("Available tables:")
        for table in tables:
            print(f"  - {table[0]}")
        
        print("\nChecking key tables for data:")
        
        # Check algorithm_learnings
        try:
            cursor.execute("SELECT COUNT(*) FROM algorithm_learnings")
            count = cursor.fetchone()[0]
            print(f"  algorithm_learnings: {count} records")
            
            if count > 0:
                cursor.execute("SELECT status, COUNT(*) FROM algorithm_learnings GROUP BY status")
                status_counts = cursor.fetchall()
                print("    Status breakdown:")
                for status, count in status_counts:
                    print(f"      {status}: {count}")
        except Exception as e:
            print(f"  algorithm_learnings: Error - {e}")
        
        # Check learning_metrics
        try:
            cursor.execute("SELECT COUNT(*) FROM learning_metrics")
            count = cursor.fetchone()[0]
            print(f"  learning_metrics: {count} records")
        except Exception as e:
            print(f"  learning_metrics: Error - {e}")
        
        # Check learned_patterns
        try:
            cursor.execute("SELECT COUNT(*) FROM learned_patterns")
            count = cursor.fetchone()[0]
            print(f"  learned_patterns: {count} records")
        except Exception as e:
            print(f"  learned_patterns: Error - {e}")
        
        # Check learning_impact_tracking
        try:
            cursor.execute("SELECT COUNT(*) FROM learning_impact_tracking")
            count = cursor.fetchone()[0]
            print(f"  learning_impact_tracking: {count} records")
        except Exception as e:
            print(f"  learning_impact_tracking: Error - {e}")
        
        conn.close()
        
    except Exception as e:
        print(f"Database error: {e}")

if __name__ == "__main__":
    check_database()
