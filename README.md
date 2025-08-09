# FlashLog - Intelligent Log Analysis and Anomaly Detection System

## Overview

FlashLog is a comprehensive log analysis and anomaly detection system that combines traditional log processing techniques with advanced AI algorithms. The system provides intelligent pattern recognition, automated anomaly detection, and detailed insights from system logs through a modern web interface.

## Key Features

### Core Analysis Capabilities
- **Multi-format Log Support**: Windows logs, Linux logs, custom formats, CSV, TXT, LOG files
- **Advanced Parsing Algorithms**: Drain, AEL, IPLOM for robust pattern recognition
- **AI-powered Anomaly Detection**: Isolation Forest, LOF, One-Class SVM, K-means, DBSCAN, BIRCH
- **Real-time Processing**: Efficient log processing with feature extraction and pattern identification
- **Learning Engine**: Continuous model improvement and adaptation

### User Interface & Experience
- **Modern Web Dashboard**: Responsive Flask-based interface with Bootstrap
- **Interactive Visualizations**: Time series charts, pattern clusters, anomaly heatmaps
- **Comprehensive Admin Panel**: User management, system monitoring, activity tracking
- **Export Capabilities**: CSV exports, detailed reports, and visualizations
- **Kibana Integration**: Advanced dashboard capabilities

### Security & Management
- **Secure Authentication**: User registration, login, password management
- **Session Management**: Robust session handling with expiration
- **Activity Logging**: Complete audit trail of all user actions
- **Role-based Access**: Admin and user roles with appropriate permissions
- **File Validation**: Secure file upload with size and format validation

## System Architecture

### Technology Stack
- **Backend**: Python Flask framework
- **Frontend**: HTML/CSS/JavaScript with Bootstrap
- **Database**: SQLite (development), supports PostgreSQL/MySQL (production)
- **AI/ML**: Custom LogAI library with scikit-learn integration
- **Deployment**: Docker support, Vercel serverless ready

### Architecture Layers
- **Presentation Layer**: Web interface, admin dashboard, user dashboard
- **Application Layer**: Authentication, analysis, user management, reporting services
- **Business Logic Layer**: Log parsing, anomaly detection, AI/ML engines
- **Data Layer**: Database, file storage, model storage
- **External Systems**: LogAI library, AI models integration

## Installation Guide

### Prerequisites
- Python 3.8 or higher
- pip package manager
- Git (for cloning the repository)

### Quick Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/NaeeemJatt/FlashLog.git
   cd FlashLog
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
   cd flashlog
   pip install -r requirements.txt
   cd ../logai
   pip install -e .
   ```

4. **Setup and run**
   ```bash
   cd ../flashlog
   python migrate_db.py
   python run.py
   ```

5. **Access the application**
   - Open browser and go to `http://localhost:5000`
   - Register a new account or use emergency admin

### Production Deployment
- Use production WSGI server (Gunicorn, uWSGI)
- Configure reverse proxy (Nginx, Apache)
- Set up SSL certificates
- Use production database (PostgreSQL, MySQL)
- Configure logging and monitoring

## Usage Guide

### For Users
1. **Registration/Login**: Create account or login with existing credentials
2. **Upload Logs**: Upload log files (max 10MB) through web interface
3. **Configure Analysis**: Select parser algorithm and detection model
4. **View Results**: Explore interactive dashboards and visualizations
5. **Export Reports**: Download analysis results in CSV format

### For Administrators
1. **User Management**: Create, edit, delete users and manage permissions
2. **System Monitoring**: View system metrics and user activities
3. **Activity Tracking**: Monitor all user actions and system performance
4. **Database Management**: Backup and maintain system data

### Command Line Interface
```python
from logai.applications.log_anomaly_detection import LogAnomalyDetection
from logai.dataloader.data_loader import DataLoader

data_loader = DataLoader()
log_data = data_loader.load_data("path/to/your/logfile.log")
anomaly_detector = LogAnomalyDetection()
results = anomaly_detector.detect_anomalies(log_data)
```

## Project Structure

```
FlashLog/
├── flashlog/                 # Main Flask web application
│   ├── app/                  # Flask application code
│   │   ├── auth.py          # Authentication and user management
│   │   ├── routes.py        # Main application routes
│   │   ├── admin.py         # Admin panel functionality
│   │   ├── dashboard.py     # Dashboard and analysis
│   │   ├── upload.py        # File upload handling
│   │   └── helpers.py       # Utility functions
│   ├── templates/           # HTML templates
│   ├── static/              # CSS, JS, and static assets
│   ├── uploads/             # User uploaded files
│   ├── requirements.txt     # Python dependencies
│   ├── run.py              # Application entry point
│   └── users.db            # SQLite database
├── logai/                   # Core log analysis library
│   ├── logai/              # Library source code
│   │   ├── applications/   # Application modules
│   │   ├── algorithms/     # Analysis algorithms
│   │   ├── dataloader/     # Data loading utilities
│   │   └── utils/          # Utility functions
│   └── setup.py            # Library setup
├── requirements.txt         # Root dependencies
└── README.md               # Project documentation
```

## Database Schema

### Core Tables
- **users**: User accounts and authentication
- **analysis_runs**: Log analysis results and metadata
- **user_activities**: Activity tracking and audit trail
- **user_sessions**: Session management
- **log_files**: File upload information
- **ai_models**: Machine learning model metadata

### Key Features
- Proper normalization and referential integrity
- JSON storage for complex analysis results
- Comprehensive audit trails
- Session management and security

## Security Features

- **Authentication**: Secure password hashing and validation
- **Session Management**: Token-based sessions with expiration
- **Input Validation**: File type and size validation
- **Activity Logging**: Complete audit trail of all actions
- **Role-based Access**: Admin and user permission levels
- **Data Protection**: Sensitive data excluded from version control

## Performance & Scalability

- **Efficient Processing**: Optimized algorithms for large log files
- **Memory Management**: Smart handling of large datasets
- **Caching**: Session and result caching for better performance
- **Modular Design**: Easy to scale and extend functionality
- **API Ready**: RESTful API structure for external integrations

## Troubleshooting

### Common Issues
- **Database Errors**: Run `python migrate_db.py` to reset database
- **Dependency Issues**: Update pip and reinstall requirements
- **Permission Errors**: Ensure proper directory permissions
- **File Upload Issues**: Check file size and format restrictions

### Support
- Check the project documentation
- Review error logs in the application
- Verify system requirements and dependencies

## Future Enhancements

- **Real-time Streaming**: Continuous log monitoring capabilities
- **Advanced AI Models**: Deep learning and transformer-based analysis
- **Cloud Integration**: AWS, Azure, and Google Cloud support
- **Mobile Application**: iOS and Android apps for monitoring
- **API Development**: RESTful APIs for external integrations
- **Advanced Analytics**: Predictive analytics and trend analysis

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is developed as part of a Final Year Project for academic purposes.

## Author

**Naeem Jatt** - [@NaeeemJatt](https://github.com/NaeeemJatt)

---

**Note**: For production deployment, additional security measures, comprehensive testing, and proper monitoring are recommended.