"""
Simple Log Anomaly Detection Module
Works directly with raw log lines without parsing or complex preprocessing.
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.svm import OneClassSVM
from sklearn.feature_extraction.text import TfidfVectorizer
import warnings
warnings.filterwarnings('ignore')

def simple_anomaly_detection(loglines, algorithm='isolation_forest', contamination=0.1):
    """
    Simple anomaly detection on raw log lines.
    
    Args:
        loglines (list): List of log lines as strings
        algorithm (str): 'isolation_forest', 'lof', or 'one_class_svm'
        contamination (float): Expected proportion of anomalies (0.0 to 0.5)
    
    Returns:
        pd.DataFrame: DataFrame with loglines and anomaly predictions
    """
    
    if not loglines:
        return pd.DataFrame({
            'logline': [],
            'is_anomaly': [],
            '_id': []
        })
    
    # Convert loglines to strings and handle None values
    loglines_clean = []
    for i, line in enumerate(loglines):
        if line is None:
            loglines_clean.append("")
        else:
            loglines_clean.append(str(line).strip())
    
    # Remove empty lines
    non_empty_indices = [i for i, line in enumerate(loglines_clean) if line]
    non_empty_lines = [loglines_clean[i] for i in non_empty_indices]
    
    if not non_empty_lines:
        # If all lines are empty, return all as normal
        return pd.DataFrame({
            'logline': loglines_clean,
            'is_anomaly': [0.0] * len(loglines_clean),
            '_id': list(range(len(loglines_clean)))
        })
    
    try:
        # Vectorize log lines using TF-IDF
        vectorizer = TfidfVectorizer(
            max_features=1000,
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.95,
            stop_words=None
        )
        
        # Fit and transform the log lines
        X = vectorizer.fit_transform(non_empty_lines)
        
        # Choose anomaly detection algorithm
        if algorithm == 'isolation_forest':
            detector = IsolationForest(
                contamination=contamination,
                random_state=42,
                n_estimators=100
            )
        elif algorithm == 'lof':
            detector = LocalOutlierFactor(
                contamination=contamination,
                n_neighbors=20,
                novelty=False
            )
        elif algorithm == 'one_class_svm':
            detector = OneClassSVM(
                nu=contamination,
                kernel='rbf',
                gamma='scale'
            )
        else:
            # Default to isolation forest
            detector = IsolationForest(
                contamination=contamination,
                random_state=42,
                n_estimators=100
            )
        
        # Fit and predict
        if algorithm == 'lof':
            # LOF doesn't have fit_predict, use fit_predict for novelty=False
            predictions = detector.fit_predict(X)
        else:
            detector.fit(X)
            predictions = detector.predict(X)
        
        # Convert predictions: -1 = anomaly, 1 = normal
        anomaly_scores = (predictions == -1).astype(float)
        
        # Create results for non-empty lines
        results = []
        for i, (idx, line, score) in enumerate(zip(non_empty_indices, non_empty_lines, anomaly_scores)):
            results.append({
                'logline': line,
                'is_anomaly': score,
                '_id': idx
            })
        
        # Add empty lines as normal (not anomalies)
        for i, line in enumerate(loglines_clean):
            if not line:  # Empty line
                results.append({
                    'logline': line,
                    'is_anomaly': 0.0,
                    '_id': i
                })
        
        # Sort by original index
        results.sort(key=lambda x: x['_id'])
        
        return pd.DataFrame(results)
        
    except Exception as e:
        print(f"❌ Error in simple anomaly detection: {e}")
        # Fallback: return all as normal
        return pd.DataFrame({
            'logline': loglines_clean,
            'is_anomaly': [0.0] * len(loglines_clean),
            '_id': list(range(len(loglines_clean)))
        }) 