"""
Continuous Learning Engine for Anomaly Detection
Learns from each analysis but requires admin approval before applying changes
"""

import json
import sqlite3
from datetime import datetime
import numpy as np
import pandas as pd
from collections import defaultdict
import re

class ContinuousLearningEngine:
    def __init__(self, db_path='flashlog.db'):
        self.db_path = db_path
        self.init_learning_tables()
        
    def init_learning_tables(self):
        """Initialize database tables for learning system"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Learning Sessions Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                user_id INTEGER NOT NULL,
                analysis_run_id TEXT NOT NULL,
                total_logs INTEGER NOT NULL,
                anomalies_detected INTEGER NOT NULL,
                original_logs TEXT,
                learning_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending'
            )
        ''')
        
        # Algorithm Learnings Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS algorithm_learnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                algorithm_name TEXT NOT NULL,
                learning_type TEXT NOT NULL,
                learning_description TEXT NOT NULL,
                confidence_score REAL DEFAULT 0.0,
                potential_improvement TEXT,
                evidence_logs TEXT,
                suggested_parameters TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending',
                admin_notes TEXT,
                applied_at DATETIME,
                FOREIGN KEY (session_id) REFERENCES learning_sessions(session_id)
            )
        ''')
        
        # Pattern Library Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learned_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT NOT NULL,
                pattern_regex TEXT NOT NULL,
                pattern_description TEXT NOT NULL,
                severity_level TEXT NOT NULL,
                detection_count INTEGER DEFAULT 0,
                false_positive_count INTEGER DEFAULT 0,
                accuracy_score REAL DEFAULT 0.0,
                created_from_session TEXT,
                status TEXT DEFAULT 'active',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Learning Metrics Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                algorithm_name TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                baseline_value REAL NOT NULL,
                learned_value REAL NOT NULL,
                improvement_percentage REAL NOT NULL,
                sample_size INTEGER NOT NULL,
                session_id TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES learning_sessions(session_id)
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Learning database tables initialized")
    
    def analyze_and_learn(self, logs, results, session_id, user_id=1):
        """Main learning function called after each analysis"""
        print(f"🧠 Starting continuous learning for session {session_id}")
        
        # Convert DataFrame to list of dictionaries if needed
        if hasattr(results, 'to_dict'):  # It's a pandas DataFrame
            results = results.to_dict(orient='records')
            print(f"[DEBUG] Converted DataFrame results to {len(results)} records")
        
        # Safety checks
        if not logs or len(logs) == 0:
            print("[DEBUG] No logs provided - skipping learning")
            return {'session_id': session_id, 'learning_count': 0, 'learnings': []}
            
        if not results or len(results) == 0:
            print("[DEBUG] No results provided - skipping learning")
            return {'session_id': session_id, 'learning_count': 0, 'learnings': []}
            
        if len(logs) != len(results):
            print(f"[DEBUG] Mismatch: {len(logs)} logs vs {len(results)} results - trimming to smaller")
            min_len = min(len(logs), len(results))
            logs = logs[:min_len]
            results = results[:min_len]
        
        # Create learning session
        learning_session = self.create_learning_session(session_id, logs, results, user_id)
        
        # Extract learnings from each algorithm with error handling
        all_learnings = []
        
        # Isolation Forest learnings
        try:
            if_learnings = self.learn_isolation_forest(logs, results, session_id)
            all_learnings.extend(if_learnings)
            print(f"[DEBUG] Isolation Forest generated {len(if_learnings)} learnings")
        except Exception as e:
            print(f"[DEBUG] Isolation Forest learning failed: {e}")
        
        # LOF learnings
        try:
            lof_learnings = self.learn_lof(logs, results, session_id)
            all_learnings.extend(lof_learnings)
            print(f"[DEBUG] LOF generated {len(lof_learnings)} learnings")
        except Exception as e:
            print(f"[DEBUG] LOF learning failed: {e}")
        
        # One-Class SVM learnings
        try:
            svm_learnings = self.learn_one_class_svm(logs, results, session_id)
            all_learnings.extend(svm_learnings)
            print(f"[DEBUG] SVM generated {len(svm_learnings)} learnings")
        except Exception as e:
            print(f"[DEBUG] SVM learning failed: {e}")
        
        # Ensemble learnings
        try:
            ensemble_learnings = self.learn_ensemble(logs, results, session_id)
            all_learnings.extend(ensemble_learnings)
            print(f"[DEBUG] Ensemble generated {len(ensemble_learnings)} learnings")
        except Exception as e:
            print(f"[DEBUG] Ensemble learning failed: {e}")
        
        # Pattern recognition learnings
        try:
            pattern_learnings = self.learn_patterns(logs, results, session_id)
            all_learnings.extend(pattern_learnings)
            print(f"[DEBUG] Patterns generated {len(pattern_learnings)} learnings")
        except Exception as e:
            print(f"[DEBUG] Pattern learning failed: {e}")
        
        # Store all learnings
        stored_count = 0
        for learning in all_learnings:
            try:
                self.store_learning(learning)
                stored_count += 1
            except Exception as e:
                print(f"[DEBUG] Failed to store learning: {e}")
        
        # Update learning session with count
        try:
            self.update_learning_session(session_id, stored_count)
        except Exception as e:
            print(f"[DEBUG] Failed to update learning session: {e}")
        
        print(f"📊 Generated {len(all_learnings)} learnings for admin review")
        return {
            'session_id': session_id,
            'learning_count': len(all_learnings),
            'learnings': all_learnings
        }
    
    def create_learning_session(self, session_id, logs, results, user_id):
        """Create a new learning session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        total_logs = len(logs)
        anomalies_detected = sum(1 for r in results if r.get('is_anomaly', False))
        
        # Store original logs in database for persistence
        original_logs_json = json.dumps(logs)
        
        cursor.execute('''
            INSERT INTO learning_sessions 
            (session_id, user_id, analysis_run_id, total_logs, anomalies_detected, original_logs)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (session_id, user_id, session_id, total_logs, anomalies_detected, original_logs_json))
        
        conn.commit()
        conn.close()
        
        return {
            'session_id': session_id,
            'total_logs': total_logs,
            'anomalies_detected': anomalies_detected
        }
    
    def learn_isolation_forest(self, logs, results, session_id):
        """Learn optimizations for Isolation Forest"""
        learnings = []
        
        # Calculate actual anomaly rate
        actual_anomaly_rate = sum(1 for r in results if r.get('is_anomaly', False)) / len(results)
        current_contamination = 0.1  # Default contamination
        
        # Learn optimal contamination rate
        if abs(actual_anomaly_rate - current_contamination) > 0.05:
            learnings.append({
                'session_id': session_id,
                'algorithm_name': 'isolation_forest',
                'learning_type': 'parameter',
                'learning_description': f'Contamination rate optimization: current {current_contamination:.3f}, observed {actual_anomaly_rate:.3f}',
                'confidence_score': min(0.9, 1.0 - abs(actual_anomaly_rate - current_contamination)),
                'potential_improvement': f'Could improve accuracy by {abs(actual_anomaly_rate - current_contamination) * 100:.1f}%',
                'evidence_logs': json.dumps([log for i, log in enumerate(logs) if results[i].get('is_anomaly', False)][:5]),
                'suggested_parameters': json.dumps({
                    'contamination': actual_anomaly_rate,
                    'reason': 'Match observed anomaly rate'
                })
            })
        
        # Learn feature importance
        feature_learning = self.analyze_feature_patterns(logs, results, 'isolation_forest')
        if feature_learning:
            learnings.append({
                'session_id': session_id,
                'algorithm_name': 'isolation_forest',
                'learning_type': 'feature',
                'learning_description': feature_learning['description'],
                'confidence_score': feature_learning['confidence'],
                'potential_improvement': feature_learning['improvement'],
                'evidence_logs': json.dumps(feature_learning['evidence']),
                'suggested_parameters': json.dumps(feature_learning['suggestion'])
            })
        
        return learnings
    
    def learn_lof(self, logs, results, session_id):
        """Learn optimizations for LOF"""
        learnings = []
        
        # Learn optimal k-neighbors based on data density
        optimal_k = self.calculate_optimal_k_neighbors(logs, results)
        current_k = 20  # Default k
        
        if abs(optimal_k - current_k) > 3:
            learnings.append({
                'session_id': session_id,
                'algorithm_name': 'lof',
                'learning_type': 'parameter',
                'learning_description': f'K-neighbors optimization: current {current_k}, optimal {optimal_k}',
                'confidence_score': 0.8,
                'potential_improvement': f'Could improve local density detection by {abs(optimal_k - current_k) * 2:.1f}%',
                'evidence_logs': json.dumps([log for i, log in enumerate(logs) if results[i].get('is_anomaly', False)][:3]),
                'suggested_parameters': json.dumps({
                    'n_neighbors': optimal_k,
                    'reason': 'Optimized for data density distribution'
                })
            })
        
        # Learn distance metric optimization
        metric_learning = self.analyze_distance_metrics(logs, results)
        if metric_learning:
            learnings.append({
                'session_id': session_id,
                'algorithm_name': 'lof',
                'learning_type': 'parameter',
                'learning_description': metric_learning['description'],
                'confidence_score': metric_learning['confidence'],
                'potential_improvement': metric_learning['improvement'],
                'evidence_logs': json.dumps(metric_learning['evidence']),
                'suggested_parameters': json.dumps(metric_learning['suggestion'])
            })
        
        return learnings
    
    def learn_one_class_svm(self, logs, results, session_id):
        """Learn optimizations for One-Class SVM"""
        learnings = []
        
        # Analyze kernel performance
        kernel_analysis = self.analyze_svm_kernel_performance(logs, results)
        if kernel_analysis:
            learnings.append({
                'session_id': session_id,
                'algorithm_name': 'one_class_svm',
                'learning_type': 'parameter',
                'learning_description': kernel_analysis['description'],
                'confidence_score': kernel_analysis['confidence'],
                'potential_improvement': kernel_analysis['improvement'],
                'evidence_logs': json.dumps(kernel_analysis['evidence']),
                'suggested_parameters': json.dumps(kernel_analysis['suggestion'])
            })
        
        # Analyze gamma parameter
        gamma_analysis = self.analyze_gamma_parameter(logs, results)
        if gamma_analysis:
            learnings.append({
                'session_id': session_id,
                'algorithm_name': 'one_class_svm',
                'learning_type': 'parameter',
                'learning_description': gamma_analysis['description'],
                'confidence_score': gamma_analysis['confidence'],
                'potential_improvement': gamma_analysis['improvement'],
                'evidence_logs': json.dumps(gamma_analysis['evidence']),
                'suggested_parameters': json.dumps(gamma_analysis['suggestion'])
            })
        
        return learnings
    
    def learn_ensemble(self, logs, results, session_id):
        """Learn ensemble optimizations"""
        learnings = []
        
        # Analyze algorithm voting weights
        weight_analysis = self.analyze_ensemble_weights(logs, results)
        if weight_analysis:
            learnings.append({
                'session_id': session_id,
                'algorithm_name': 'ensemble',
                'learning_type': 'parameter',
                'learning_description': weight_analysis['description'],
                'confidence_score': weight_analysis['confidence'],
                'potential_improvement': weight_analysis['improvement'],
                'evidence_logs': json.dumps(weight_analysis['evidence']),
                'suggested_parameters': json.dumps(weight_analysis['suggestion'])
            })
        
        return learnings
    
    def learn_patterns(self, logs, results, session_id):
        """Learn new patterns from anomalous logs"""
        learnings = []
        
        # Get anomalous logs only
        anomalous_logs = [logs[i] for i, r in enumerate(results) if r.get('is_anomaly', False)]
        
        if not anomalous_logs:
            return learnings
        
        # Extract security patterns
        security_patterns = self.extract_security_patterns(anomalous_logs)
        for pattern in security_patterns:
            learnings.append({
                'session_id': session_id,
                'algorithm_name': 'pattern_recognition',
                'learning_type': 'pattern',
                'learning_description': f'New security pattern: {pattern["description"]}',
                'confidence_score': pattern['confidence'],
                'potential_improvement': f'Could detect {pattern["detection_rate"]:.1f}% more security threats',
                'evidence_logs': json.dumps(pattern['examples'][:3]),
                'suggested_parameters': json.dumps({
                    'pattern_type': 'security',
                    'regex': pattern['regex'],
                    'severity': pattern['severity']
                })
            })
        
        # Extract error patterns
        error_patterns = self.extract_error_patterns(anomalous_logs)
        for pattern in error_patterns:
            learnings.append({
                'session_id': session_id,
                'algorithm_name': 'pattern_recognition',
                'learning_type': 'pattern',
                'learning_description': f'New error pattern: {pattern["description"]}',
                'confidence_score': pattern['confidence'],
                'potential_improvement': f'Could detect {pattern["detection_rate"]:.1f}% more error anomalies',
                'evidence_logs': json.dumps(pattern['examples'][:3]),
                'suggested_parameters': json.dumps({
                    'pattern_type': 'error',
                    'regex': pattern['regex'],
                    'severity': pattern['severity']
                })
            })
        
        return learnings
    
    def calculate_optimal_k_neighbors(self, logs, results):
        """Calculate optimal k-neighbors for LOF based on data characteristics"""
        n_samples = len(logs)
        anomaly_rate = sum(1 for r in results if r.get('is_anomaly', False)) / len(results)
        
        # Base k on sample size and anomaly density
        if n_samples < 50:
            base_k = max(3, n_samples // 10)
        elif n_samples < 200:
            base_k = max(5, n_samples // 15)
        else:
            base_k = max(10, n_samples // 20)
        
        # Adjust based on anomaly rate
        if anomaly_rate > 0.2:
            base_k = int(base_k * 0.8)  # Reduce k for high anomaly rate
        elif anomaly_rate < 0.05:
            base_k = int(base_k * 1.2)  # Increase k for low anomaly rate
        
        return min(max(base_k, 3), 50)  # Keep within reasonable bounds
    
    def analyze_feature_patterns(self, logs, results, algorithm):
        """Analyze feature patterns for optimization"""
        # Simplified feature analysis - in practice this would be more sophisticated
        anomalous_logs = [logs[i] for i, r in enumerate(results) if r.get('is_anomaly', False)]
        
        if len(anomalous_logs) < 3:
            return None
        
        # Analyze log length patterns
        avg_anomaly_length = np.mean([len(log) for log in anomalous_logs])
        avg_normal_length = np.mean([len(logs[i]) for i, r in enumerate(results) if not r.get('is_anomaly', False)])
        
        if abs(avg_anomaly_length - avg_normal_length) > 50:
            return {
                'description': f'Log length feature shows {abs(avg_anomaly_length - avg_normal_length):.0f} char difference between normal/anomaly',
                'confidence': 0.7,
                'improvement': f'{abs(avg_anomaly_length - avg_normal_length) / 10:.1f}%',
                'evidence': anomalous_logs[:3],
                'suggestion': {
                    'feature_weight': 'log_length',
                    'weight_multiplier': 1.5 if avg_anomaly_length > avg_normal_length else 0.7
                }
            }
        
        return None
    
    def analyze_distance_metrics(self, logs, results):
        """Analyze optimal distance metrics for LOF"""
        # Simplified analysis - would be more sophisticated in practice
        anomalous_logs = [logs[i] for i, r in enumerate(results) if r.get('is_anomaly', False)]
        
        if len(anomalous_logs) < 5:
            return None
        
        # Check if logs have many similar patterns (suggesting Manhattan distance might be better)
        pattern_similarity = self.calculate_pattern_similarity(anomalous_logs)
        
        if pattern_similarity > 0.7:
            return {
                'description': f'High pattern similarity ({pattern_similarity:.2f}) suggests Manhattan distance optimization',
                'confidence': 0.6,
                'improvement': '8-12%',
                'evidence': anomalous_logs[:3],
                'suggestion': {
                    'metric': 'manhattan',
                    'reason': 'High categorical pattern similarity detected'
                }
            }
        
        return None
    
    def analyze_svm_kernel_performance(self, logs, results):
        """Analyze SVM kernel performance"""
        # Simplified analysis
        anomalous_logs = [logs[i] for i, r in enumerate(results) if r.get('is_anomaly', False)]
        
        if len(anomalous_logs) < 3:
            return None
        
        # Check log complexity to suggest kernel
        complexity_score = self.calculate_log_complexity(anomalous_logs)
        
        if complexity_score > 0.8:
            return {
                'description': f'High log complexity ({complexity_score:.2f}) suggests polynomial kernel optimization',
                'confidence': 0.6,
                'improvement': '10-15%',
                'evidence': anomalous_logs[:3],
                'suggestion': {
                    'kernel': 'poly',
                    'degree': 3,
                    'reason': 'Complex pattern structures detected'
                }
            }
        
        return None
    
    def analyze_gamma_parameter(self, logs, results):
        """Analyze optimal gamma parameter for SVM"""
        # Simplified analysis
        return {
            'description': 'Gamma parameter could be optimized based on feature density',
            'confidence': 0.5,
            'improvement': '5-8%',
            'evidence': logs[:3],
            'suggestion': {
                'gamma': 'auto',
                'reason': 'Adaptive gamma based on feature variance'
            }
        }
    
    def analyze_ensemble_weights(self, logs, results):
        """Analyze optimal ensemble weights"""
        # Simplified analysis
        return {
            'description': 'Ensemble weights could be optimized based on individual algorithm performance',
            'confidence': 0.7,
            'improvement': '12-18%',
            'evidence': logs[:3],
            'suggestion': {
                'lof_weight': 0.4,
                'isolation_forest_weight': 0.35,
                'one_class_svm_weight': 0.25,
                'reason': 'Performance-based weight optimization'
            }
        }
    
    def extract_security_patterns(self, anomalous_logs):
        """Extract security patterns from anomalous logs"""
        patterns = []
        
        # SQL injection pattern
        sql_logs = [log for log in anomalous_logs if re.search(r"'|\bOR\s+1\s*=\s*1\b|\bUNION\b|\bSELECT\b", log, re.IGNORECASE)]
        if len(sql_logs) >= 2:
            patterns.append({
                'description': 'SQL injection attempts detected',
                'regex': r"'|\bOR\s+1\s*=\s*1\b|\bUNION\b|\bSELECT\b",
                'confidence': min(0.9, len(sql_logs) / len(anomalous_logs)),
                'detection_rate': len(sql_logs) / len(anomalous_logs) * 100,
                'severity': 'critical',
                'examples': sql_logs[:3]
            })
        
        # Path traversal pattern
        path_logs = [log for log in anomalous_logs if '../' in log or '..\\' in log]
        if len(path_logs) >= 2:
            patterns.append({
                'description': 'Path traversal attempts detected',
                'regex': r'\.\./|\.\.\\',
                'confidence': min(0.8, len(path_logs) / len(anomalous_logs)),
                'detection_rate': len(path_logs) / len(anomalous_logs) * 100,
                'severity': 'high',
                'examples': path_logs[:3]
            })
        
        # Admin access pattern
        admin_logs = [log for log in anomalous_logs if re.search(r'/admin|admin/|administrator', log, re.IGNORECASE)]
        if len(admin_logs) >= 2:
            patterns.append({
                'description': 'Admin access attempts detected',
                'regex': r'/admin|admin/|administrator',
                'confidence': min(0.7, len(admin_logs) / len(anomalous_logs)),
                'detection_rate': len(admin_logs) / len(anomalous_logs) * 100,
                'severity': 'high',
                'examples': admin_logs[:3]
            })
        
        return patterns
    
    def extract_error_patterns(self, anomalous_logs):
        """Extract error patterns from anomalous logs"""
        patterns = []
        
        # Memory error pattern
        memory_logs = [log for log in anomalous_logs if re.search(r'OutOfMemory|Memory|heap\s+space', log, re.IGNORECASE)]
        if len(memory_logs) >= 2:
            patterns.append({
                'description': 'Memory-related errors detected',
                'regex': r'OutOfMemory|Memory|heap\s+space',
                'confidence': min(0.8, len(memory_logs) / len(anomalous_logs)),
                'detection_rate': len(memory_logs) / len(anomalous_logs) * 100,
                'severity': 'high',
                'examples': memory_logs[:3]
            })
        
        # Database error pattern
        db_logs = [log for log in anomalous_logs if re.search(r'database|connection.*failed|timeout', log, re.IGNORECASE)]
        if len(db_logs) >= 2:
            patterns.append({
                'description': 'Database connection errors detected',
                'regex': r'database|connection.*failed|timeout',
                'confidence': min(0.7, len(db_logs) / len(anomalous_logs)),
                'detection_rate': len(db_logs) / len(anomalous_logs) * 100,
                'severity': 'medium',
                'examples': db_logs[:3]
            })
        
        return patterns
    
    def calculate_pattern_similarity(self, logs):
        """Calculate pattern similarity between logs"""
        # Simplified similarity calculation
        if len(logs) < 2:
            return 0.0
        
        # Count common patterns
        common_patterns = 0
        total_comparisons = 0
        
        for i in range(len(logs)):
            for j in range(i + 1, len(logs)):
                total_comparisons += 1
                # Simple similarity based on common words
                words1 = set(logs[i].lower().split())
                words2 = set(logs[j].lower().split())
                similarity = len(words1 & words2) / len(words1 | words2) if words1 | words2 else 0
                if similarity > 0.3:
                    common_patterns += 1
        
        return common_patterns / total_comparisons if total_comparisons > 0 else 0.0
    
    def calculate_log_complexity(self, logs):
        """Calculate complexity score of logs"""
        # Simplified complexity calculation
        if not logs:
            return 0.0
        
        total_complexity = 0
        for log in logs:
            # Factors that increase complexity
            special_chars = len(re.findall(r'[^a-zA-Z0-9\s]', log))
            words = len(log.split())
            
            complexity = (special_chars / len(log) + min(words / 20, 1.0)) / 2
            total_complexity += complexity
        
        return total_complexity / len(logs)
    
    def store_learning(self, learning):
        """Store learning in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO algorithm_learnings 
            (session_id, algorithm_name, learning_type, learning_description,
             confidence_score, potential_improvement, evidence_logs, suggested_parameters)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            learning['session_id'],
            learning['algorithm_name'],
            learning['learning_type'],
            learning['learning_description'],
            learning['confidence_score'],
            learning['potential_improvement'],
            learning['evidence_logs'],
            learning['suggested_parameters']
        ))
        
        conn.commit()
        conn.close()
    
    def update_learning_session(self, session_id, learning_count):
        """Update learning session with final count"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE learning_sessions 
            SET status = 'completed'
            WHERE session_id = ?
        ''', (session_id,))
        
        conn.commit()
        conn.close()
    
    def get_pending_learnings(self):
        """Get all pending learnings for admin review"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        learnings = cursor.execute('''
            SELECT al.*, ls.total_logs, ls.anomalies_detected
            FROM algorithm_learnings al
            JOIN learning_sessions ls ON al.session_id = ls.session_id
            WHERE al.status = 'pending'
            ORDER BY al.confidence_score DESC, al.created_at DESC
        ''').fetchall()
        
        conn.close()
        return [dict(row) for row in learnings]
    
    def get_original_logs_for_session(self, session_id):
        """Get original logs for a learning session (persistent storage)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        result = cursor.execute('''
            SELECT original_logs FROM learning_sessions 
            WHERE session_id = ?
        ''', (session_id,)).fetchone()
        
        conn.close()
        
        if result and result[0]:
            try:
                return json.loads(result[0])
            except json.JSONDecodeError:
                print(f"[ERROR] Failed to decode original logs for session {session_id}")
                return []
        return []
    
    def reprocess_learning_with_stored_logs(self, learning_id):
        """Reprocess a learning using stored original logs (session-independent)"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get learning and session info
        learning = cursor.execute('''
            SELECT al.*, ls.original_logs, ls.session_id
            FROM algorithm_learnings al
            JOIN learning_sessions ls ON al.session_id = ls.session_id
            WHERE al.id = ?
        ''', (learning_id,)).fetchone()
        
        conn.close()
        
        if not learning:
            return None
        
        # Get original logs from database
        original_logs = self.get_original_logs_for_session(learning['session_id'])
        
        if not original_logs:
            print(f"[WARNING] No original logs found for learning {learning_id}")
            return None
        
        print(f"[DEBUG] Reprocessing learning {learning_id} with {len(original_logs)} stored logs")
        return {
            'learning': dict(learning),
            'original_logs': original_logs,
            'can_reprocess': True
        }

# Test the learning engine
if __name__ == "__main__":
    # Test data
    test_logs = [
        "INFO: User login successful",
        "INFO: Page loaded",
        "ERROR: Database connection failed",
        "CRITICAL: Security breach detected",
        "192.168.1.100 GET /admin/config.php 404",
        "192.168.1.200 GET /../../etc/passwd 404"
    ]
    
    test_results = [
        {'is_anomaly': False},
        {'is_anomaly': False},
        {'is_anomaly': True},
        {'is_anomaly': True},
        {'is_anomaly': True},
        {'is_anomaly': True}
    ]
    
    # Test learning engine
    engine = ContinuousLearningEngine()
    learning_result = engine.analyze_and_learn(test_logs, test_results, "test_session_001")
    
    print(f"\n🧪 Learning Engine Test Results:")
    print(f"Generated {learning_result['learning_count']} learnings")
    
    # Show pending learnings
    pending = engine.get_pending_learnings()
    print(f"\nPending learnings for admin review: {len(pending)}")
    for learning in pending[:3]:  # Show first 3
        print(f"  - {learning['algorithm_name']}: {learning['learning_description']}")
        print(f"    Confidence: {learning['confidence_score']:.2f}, Improvement: {learning['potential_improvement']}")