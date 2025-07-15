import sqlite3

conn = sqlite3.connect('users.db')
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS user_activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    activity_type TEXT NOT NULL,
    description TEXT NOT NULL,
    details TEXT,
    status TEXT DEFAULT 'success',
    ip_address TEXT,
    user_agent TEXT,
    file_name TEXT,
    file_size INTEGER,
    processing_time REAL,
    anomalies_detected INTEGER,
    total_logs INTEGER,
    old_value TEXT,
    new_value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')
conn.commit()
print('✅ user_activities table ensured.')
conn.close() 