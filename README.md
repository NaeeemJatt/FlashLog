# FYP - Log Analysis and Anomaly Detection using AI

## Overview

This Final Year Project implements an intelligent log analysis and anomaly detection system using artificial intelligence. The system combines traditional log processing techniques with advanced AI algorithms to identify patterns, detect anomalies, and provide insights from system logs.

## Features

### �� **Log Analysis**
- Multi-format log support (Windows, Linux, custom formats)
- Intelligent parsing algorithms (Drain, AEL, IPLOM)
- Pattern recognition and feature extraction
- Real-time processing capabilities

### 🚨 **Anomaly Detection**
- Multiple detection algorithms (Isolation Forest, LOF, One-Class SVM)
- Neural network approaches (LSTM, CNN, Transformer)
- Configurable sensitivity thresholds
- Real-time anomaly detection

### 🎯 **Clustering & Classification**
- Log clustering with K-means, DBSCAN, BIRCH
- Semantic analysis using word embeddings
- Categorical data handling

### 🌐 **Web Interface**
- User-friendly Flask-based GUI
- File upload and processing
- Real-time result visualization
- Interactive dashboards

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/NaeeemJatt/FYP-Log-Analysis-and-Anomaly-Detection-using-AI.git
   cd FYP-Log-Analysis-and-Anomaly-Detection-using-AI
   ```

2. **Setup virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies**
   ```bash
   cd FYP_GUI
   pip install -r requirements.txt
   cd ../logai
   pip install -e .
   ```

## Usage

### Web Application
```bash
cd FYP_GUI
python run.py
```
Then visit `http://localhost:5000` in your browser.

### Command Line
```python
from logai.applications.log_anomaly_detection import LogAnomalyDetection
anomaly_detector = LogAnomalyDetection()
results = anomaly_detector.detect_anomalies(log_data)
```

## Project Structure
```
FYP/
├── FYP_GUI/          # Web application
├── logai/            # Core analysis library
├── logs/             # Sample log files
└── README.md
```

## Author
**Naeem Jatt** - [@NaeeemJatt](https://github.com/NaeeemJatt)

## License
MIT License