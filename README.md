# FYP - Log Analysis and Anomaly Detection using AI

## Overview

This Final Year Project implements an intelligent log analysis and anomaly detection system using artificial intelligence. The system combines traditional log processing techniques with advanced AI algorithms to identify patterns, detect anomalies, and provide insights from system logs.

## Features

### 🔍 **Log Analysis**
- **Multi-format Log Support**: Handles various log formats including Windows Event Logs, Linux system logs, and custom log formats
- **Intelligent Parsing**: Advanced log parsing algorithms (Drain, AEL, IPLOM) to extract structured information
- **Pattern Recognition**: Identifies common patterns and sequences in log data
- **Feature Extraction**: Extracts meaningful features for analysis

### 🚨 **Anomaly Detection**
- **Multiple Detection Algorithms**:
  - Isolation Forest
  - Local Outlier Factor (LOF)
  - One-Class SVM
  - Distribution-based methods
  - Neural Network-based approaches (LSTM, CNN, Transformer)
- **Real-time Detection**: Capable of detecting anomalies in streaming log data
- **Configurable Thresholds**: Adjustable sensitivity levels for different environments

### 🎯 **Clustering & Classification**
- **Log Clustering**: Groups similar log entries using algorithms like K-means, DBSCAN, BIRCH
- **Semantic Analysis**: Understands log semantics using word embeddings and NLP techniques
- **Categorical Encoding**: Handles categorical data in logs effectively

### 🌐 **Web Interface**
- **User-friendly GUI**: Modern web interface built with Flask
- **File Upload**: Easy log file upload and processing
- **Real-time Results**: Instant visualization of analysis results
- **Interactive Dashboards**: Charts and graphs for better understanding

## Project Structure

```
FYP/
├── FYP_GUI/                 # Web application
│   ├── app/                 # Flask application
│   ├── templates/           # HTML templates
│   ├── uploads/            # Uploaded log files
│   └── requirements.txt    # Python dependencies
├── logai/                  # Core log analysis library
│   ├── algorithms/         # AI algorithms
│   ├── applications/       # Application workflows
│   ├── dataloader/         # Data loading utilities
│   ├── gui/               # GUI components
│   └── utils/             # Utility functions
├── logs/                  # Sample log files
└── run_logai_to_elasticsearch.py  # Elasticsearch integration
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
   cd FYP_GUI
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
   cd FYP_GUI
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

# Load log data
data_loader = DataLoader()
log_data = data_loader.load_data("path/to/your/logfile.log")

# Initialize anomaly detection
anomaly_detector = LogAnomalyDetection()

# Detect anomalies
results = anomaly_detector.detect_anomalies(log_data)
```

## Supported Log Formats

- **Windows Event Logs**: .evtx files
- **Linux System Logs**: /var/log/* files
- **Application Logs**: Custom formats
- **CSV/JSON**: Structured log data
- **Plain Text**: Unstructured log files

## Algorithms

### Anomaly Detection
- **Statistical Methods**: Z-score, IQR-based detection
- **Machine Learning**: Isolation Forest, LOF, One-Class SVM
- **Deep Learning**: LSTM, CNN, Transformer models
- **Ensemble Methods**: Combining multiple algorithms

### Log Parsing
- **Drain**: Template-based parsing
- **AEL**: Advanced log parsing
- **IPLOM**: Iterative partitioning log mining

### Clustering
- **K-means**: Centroid-based clustering
- **DBSCAN**: Density-based clustering
- **BIRCH**: Hierarchical clustering

## Configuration

The system supports various configuration options:

```yaml
# Example configuration
anomaly_detection:
  algorithm: "isolation_forest"
  contamination: 0.1
  random_state: 42

clustering:
  algorithm: "kmeans"
  n_clusters: 10

parsing:
  algorithm: "drain"
  max_depth: 4
  max_child: 100
```

## Results and Outputs

- **Anomaly Reports**: Detailed analysis of detected anomalies
- **Clustering Results**: Grouped log patterns and insights
- **Visualizations**: Charts, graphs, and interactive plots
- **Export Options**: CSV, JSON, and PDF reports

## Performance

- **Scalability**: Handles large log files efficiently
- **Speed**: Optimized algorithms for real-time processing
- **Memory**: Efficient memory usage for big data
- **Accuracy**: High precision and recall in anomaly detection

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

**Naeem Jatt**
- GitHub: [@NaeeemJatt](https://github.com/NaeeemJatt)
- Focus: Cybersecurity and Ethical Hacking

## Acknowledgments

- LogAI library contributors
- Open-source community
- Academic research in log analysis and anomaly detection

## Future Enhancements

- [ ] Real-time streaming analysis
- [ ] Advanced visualization dashboards
- [ ] Integration with SIEM systems
- [ ] Machine learning model training interface
- [ ] Support for more log formats
- [ ] Performance optimization for large-scale deployments

---

**Note**: This project is developed as part of a Final Year Project for academic purposes. For production use, additional security measures and testing are recommended.