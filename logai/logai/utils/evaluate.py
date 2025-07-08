
import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score

def get_accuracy_precision_recall(y: np.array, y_labels: np.array):
    
    if len(y) != len(y_labels):
        raise IndexError("The length of anomalies and labels should be the same")

    accuracy = accuracy_score(y, y_labels)
    precision = precision_score(y, y_labels)
    recall = recall_score(y, y_labels)
    return accuracy, precision, recall
