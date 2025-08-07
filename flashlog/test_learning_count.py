import sqlite3

def test_learning_count():
    try:
        conn = sqlite3.connect('flashlog.db')
        cursor = conn.cursor()
        
        # Get all pending learnings with details
        cursor.execute('''
            SELECT id, algorithm_name, learning_type, confidence_score, status, created_at
            FROM algorithm_learnings 
            WHERE status = 'pending'
            ORDER BY created_at DESC
        ''')
        
        pending_learnings = cursor.fetchall()
        
        print(f"Total pending learnings in database: {len(pending_learnings)}")
        print("\nPending learning details:")
        for i, learning in enumerate(pending_learnings, 1):
            print(f"  {i}. ID: {learning[0]}, Algorithm: {learning[1]}, Type: {learning[2]}, Confidence: {learning[3]:.2f}, Created: {learning[5]}")
        
        # Check if there are any learnings with unexpected status
        cursor.execute('''
            SELECT status, COUNT(*) 
            FROM algorithm_learnings 
            GROUP BY status
        ''')
        
        status_counts = cursor.fetchall()
        print(f"\nAll status counts:")
        for status, count in status_counts:
            print(f"  {status}: {count}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_learning_count()
