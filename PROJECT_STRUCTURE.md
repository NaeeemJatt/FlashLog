# FYP Project Structure

## Current Codebase Layout

```
FYP/
├── api/                      # API entrypoint for serverless deployment
│   └── index.py             # Vercel serverless function
│
├── flashlog/                 # Main Flask web application
│   ├── app/                 # Flask application core
│   │   ├── __init__.py      # App factory and configuration
│   │   ├── auth.py          # Authentication and user management
│   │   ├── admin.py         # Admin panel functionality
│   │   ├── routes.py        # Main application routes
│   │   └── logai_handler.py # LogAI integration handler
│   ├── templates/           # HTML templates
│   │   ├── index.html       # Main dashboard
│   │   ├── analyzed_logs.html # Results display
│   │   ├── history.html     # User activity history
│   │   ├── auth/            # Authentication templates
│   │   ├── admin/           # Admin panel templates
│   │   └── errors/          # Error page templates
│   ├── uploads/             # User uploaded files (auto-generated)
│   ├── flashlog/            # Database and backup files (excluded from git)
│   ├── run.py               # Application entry point
│   ├── requirements.txt     # Flask app dependencies
│   ├── create_emergency_admin.py # Emergency admin creation script
│   ├── EMERGENCY_ADMIN_README.md # Emergency admin documentation
│   ├── SECURITY.md          # Security documentation
│   ├── TODO_NEXT.md         # Development roadmap
│   ├── env_example.txt      # Environment configuration template
│   ├── users.db             # SQLite database (excluded from git)
│   ├── check_activities.py  # Activity monitoring script
│   ├── ensure_user_activities_table.py # Database setup script
│   ├── test_activities.py   # Activity testing script
│   ├── migrate_db.py        # Database migration script
│   └── test_upload.html     # Upload testing page
│
├── logai/                    # Core log analysis library
│   ├── logai/               # Main library code
│   │   ├── algorithms/      # AI algorithms implementation
│   │   │   ├── anomaly_detection_algo/ # Anomaly detection algorithms
│   │   │   ├── clustering_algo/        # Clustering algorithms
│   │   │   ├── parsing_algo/           # Log parsing algorithms
│   │   │   ├── vectorization_algo/     # Vectorization algorithms
│   │   │   └── nn_model/               # Neural network models
│   │   ├── applications/    # Application workflows
│   │   ├── analysis/        # Analysis components
│   │   ├── dataloader/      # Data loading utilities
│   │   ├── information_extraction/ # Feature extraction
│   │   ├── preprocess/      # Data preprocessing
│   │   ├── utils/           # Utility functions
│   │   └── config_interfaces.py # Configuration interfaces
│   └── tests/               # Library tests
│
├── scripts/                  # Utility scripts
│   └── run_logai_to_elasticsearch.py # Elasticsearch integration
│
├── logs/                     # Sample log files (optional)
│   ├── Android_2k.log_structured.csv
│   ├── BGL_2k.log
│   ├── Hadoop_2k.log_structured.csv
│   ├── HDFS_2k.log_structured.csv
│   ├── Linux_2k.log
│   ├── Windows_2k.log_structured.csv
│   └── logfile.csv
│
├── .venv/                    # Virtual environment (excluded from git)
├── .git/                     # Git repository
├── .gitignore                # Git ignore rules
├── requirements.txt          # Root dependencies
├── README.md                 # Project documentation
├── PROJECT_STRUCTURE.md      # This file
├── DEPLOYMENT.md             # Deployment guide
├── .vercelignore             # Vercel ignore rules
└── vercel.json               # Vercel configuration
```

## Key Components

### 1. Web Application (flashlog/)
- **Flask-based web interface** for log upload and analysis
- **User authentication system** with admin panel
- **Real-time log processing** and anomaly detection
- **Interactive dashboards** for results visualization
- **User activity tracking** and history

### 2. Core Library (logai/)
- **Comprehensive log analysis algorithms**
- **Multiple anomaly detection methods** (Isolation Forest, LOF, One-Class SVM)
- **Advanced log parsing** (Drain, AEL, IPLOM)
- **Clustering algorithms** (K-means, DBSCAN, BIRCH)
- **Neural network models** (LSTM, CNN, Transformer)

### 3. API Layer (api/)
- **Serverless deployment support** via Vercel
- **RESTful API endpoints** for log processing
- **Scalable architecture** for production use

### 4. Sample Data (logs/)
- **Various log formats** for testing and demonstration
- **Structured and unstructured logs**
- **Different system types** (Windows, Linux, Android, etc.)

## Security Features

- **Comprehensive .gitignore** protecting sensitive files
- **Database files excluded** from version control
- **Environment configuration** templates provided
- **Emergency admin access** script for recovery
- **User session management** with secure tokens

## Development Workflow

1. **Local Development**: Use `flashlog/run.py` for local testing
2. **Library Development**: Work in `logai/` directory
3. **Testing**: Use sample logs in `logs/` directory
4. **Deployment**: Use Vercel configuration for production

## File Organization Benefits

- **Clear separation** between web app and core library
- **Modular architecture** for easy maintenance
- **Production-ready structure** with proper security
- **Scalable design** supporting multiple deployment options

The codebase is now clean, secure, and production-ready! 