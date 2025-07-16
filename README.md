# FYP - Log Analysis and Anomaly Detection using AI

## Overview

This project implements an intelligent log analysis and anomaly detection system using artificial intelligence. It combines traditional log processing techniques with advanced AI algorithms to identify patterns, detect anomalies, and provide insights from system logs.

## Features

- **Multi-format Log Support**: Handles various log formats (Windows, Linux, custom)
- **Intelligent Parsing**: Advanced log parsing algorithms (Drain, AEL, IPLOM)
- **Pattern Recognition**: Identifies common patterns and sequences
- **Feature Extraction**: Extracts meaningful features for analysis
- **Anomaly Detection**: Isolation Forest, LOF, One-Class SVM, Neural Networks (LSTM, CNN, Transformer)
- **Clustering**: K-means, DBSCAN, BIRCH
- **Web Interface**: Modern Flask-based GUI for log upload and analysis

## Project Structure

```
FYP/
├── api/                  # API entrypoint (for serverless deployment)
├── flashlog/             # Main Flask web application
│   ├── app/              # Flask app code
│   ├── templates/        # HTML templates
│   └── requirements.txt  # Python dependencies
├── logai/                # Core log analysis library
│   └── logai/            # Main library code
├── scripts/              # Utility scripts
├── logs/                 # (Optional) Sample log files (not required for production)
├── requirements.txt      # Root dependencies
├── .gitignore            # Git ignore rules
└── README.md             # Project documentation
```

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/NaeeemJatt/FYP-Log-Analysis-and-Anomaly-Detection-using-AI.git
   cd FYP-Log-Analysis-and-Anomaly-Detection-using-AI
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   cd flashlog
   pip install -r requirements.txt
   ```

4. **Install logai library**
   ```bash
   cd ../logai
   pip install -e .
   ```

## Usage

### Web Application

1. **Start the web server**
   ```bash
   cd flashlog
   python run.py
   ```

2. **Access the application**
   - Open your browser and go to `http://localhost:5000`
   - Upload your log files through the web interface
   - Configure analysis parameters
   - View results and visualizations

### Command Line Usage

```python
from logai.applications.log_anomaly_detection import LogAnomalyDetection
from logai.dataloader.data_loader import DataLoader

data_loader = DataLoader()
log_data = data_loader.load_data("path/to/your/logfile.log")
anomaly_detector = LogAnomalyDetection()
results = anomaly_detector.detect_anomalies(log_data)
```

## Security Notes
- All sensitive files (databases, backups, environment configs) are now excluded from version control via `.gitignore`.
- No test or upload directories are present in production.
- For emergency admin access, see the `flashlog/create_emergency_admin.py` script (excluded from git).

## Author
**Naeem Jatt** - [@NaeeemJatt](https://github.com/NaeeemJatt)

---
**Note**: This project is developed as part of a Final Year Project for academic purposes. For production use, additional security measures and testing are recommended.