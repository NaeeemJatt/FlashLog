#!/usr/bin/env python3
"""
Create sample learning data for testing the admin dashboard
"""

import sqlite3
import json
from datetime import datetime

def create_sample_data():
    """Create sample learning data"""
    conn = sqlite3.connect('flashlog/flashlog.db')
    cursor = conn.cursor()
    
    # Create sample session
    session_id = f'test_session_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    user_id = 1
    total_logs = 1000
    anomalies_detected = 45
    
    # Insert learning session
    cursor.execute('''
        INSERT INTO learning_sessions (session_id, user_id, analysis_run_id, total_logs, anomalies_detected, original_logs)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (session_id, user_id, session_id, total_logs, anomalies_detected, 
          json.dumps(['sample log entry 1', 'sample log entry 2'])))
    
    # Insert sample algorithm learning
    cursor.execute('''
        INSERT INTO algorithm_learnings 
        (session_id, algorithm_name, learning_type, learning_description, confidence_score, potential_improvement, evidence_logs, suggested_parameters)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        session_id, 
        'isolation_forest', 
        'parameter', 
        'Contamination rate optimization: current 0.100, observed 0.034',
        0.90,
        'Could improve accuracy by 6.6%',
        json.dumps([
            '111876723 2005.06.14 R20-M1-N3-C:J14-U01 2005-06-14-09.41.23.815131 R20-M1-N3-C:J14-U01 RAS KERNEL FATAL machine check: 1-fetch..................0',
            'APPREAD 111756973 2005.06.04 R04-M1-N4-I:J18-U11 2005-06-04-00.24.32.432132 R04-M1-N4-I:J18-U11 R&3 APP FATAL eid[ald: failed to read message prefix on Control System'
        ]),
        json.dumps({'contamination': 0.034, 'reason': 'Match observed anomaly rate'})
    ))
    
    # Insert another learning example
    cursor.execute('''
        INSERT INTO algorithm_learnings 
        (session_id, algorithm_name, learning_type, learning_description, confidence_score, potential_improvement, evidence_logs, suggested_parameters)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        session_id, 
        'lof', 
        'pattern', 
        'Memory fault pattern detection improvement',
        0.85,
        'Could reduce false positives by 12%',
        json.dumps([
            'EDRAMCOR 111876900 2005.06.14 R20-M1-N3-C:J14-U01 2005-06-14-09.41.28.832012 R20-M1-N3-C:J14-U01 RAS KERNEL INFO machine check: 0-fetch..................0',
            'EDRAMCOR 111877445 2005.06.14 R20-M1-N3-C:J15-U01 2005-06-14-09.42.15.402301 R20-M1-N3-C:J15-U01 RAS KERNEL INFO machine check: 0-fetch..................0'
        ]),
        json.dumps({'n_neighbors': 25, 'reason': 'Better local density estimation'})
    ))
    
    # Insert sample metrics
    cursor.execute('''
        INSERT INTO learning_metrics 
        (algorithm_name, metric_name, baseline_value, learned_value, improvement_percentage, sample_size, session_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', ('isolation_forest', 'accuracy', 0.82, 0.87, 6.1, 1000, session_id))
    
    cursor.execute('''
        INSERT INTO learning_metrics 
        (algorithm_name, metric_name, baseline_value, learned_value, improvement_percentage, sample_size, session_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', ('lof', 'precision', 0.75, 0.84, 12.0, 1000, session_id))
    
    conn.commit()
    conn.close()
    
    print(f'✅ Sample learning data created with session_id: {session_id}')
    return session_id

if __name__ == '__main__':
    create_sample_data()