from logai.applications.log_anomaly_detection import LogAnomalyDetection
from logai.applications.application_interfaces import WorkFlowConfig
from logai.analysis.anomaly_detector import AnomalyDetectionConfig
from logai.dataloader.openset_data_loader import OpenSetDataLoaderConfig
from logai.information_extraction.log_parser import LogParserConfig
from logai.information_extraction.feature_extractor import FeatureExtractorConfig
from logai.information_extraction.categorical_encoder import CategoricalEncoderConfig
from elasticsearch import Elasticsearch
from datetime import datetime

def send_to_elasticsearch(index_name, result_list):
    from elasticsearch import Elasticsearch

    es = Elasticsearch(
        "http://localhost:9200",
        headers={"Accept": "application/vnd.elasticsearch+json; compatible-with=8",
                "Content-Type": "application/vnd.elasticsearch+json; compatible-with=8"}
    )
    for _, result in result_list.iterrows():
        doc = {
            "log_line": result.get("logline"),
            "anomaly": result.get("is_anomaly", False),
            "score": 1.0 if result.get("is_anomaly", False) else 0.0,
            "timestamp": result.get("timestamp", datetime.utcnow().isoformat())
        }
        es.index(index=index_name, document=doc)

# ✅ Correct config using from_dict()
config = WorkFlowConfig.from_dict({
    "data_loader_config": {
        "filepath": "C:/Users/AbdulRehman/Desktop/FYP/logs/logfile.csv",
        "dimensions": {
            "body": ["logline"],
            "timestamp": ["timestamp"]
        }
    },
    "preprocessor_config": {
        "custom_delimiters_regex": []
    },
    "log_parser_config": {
        "parsing_algorithm": "drain"
    },
    "log_vectorizer_config": {
        "algo_name": "tfidf"
    },
    "categorical_encoder_config": {
        "encoding_type": "onehot"
    },
    "feature_extractor_config": {
        "feature_type": "log_vector",
        "window_size": 5,
        "embedding_method": "tfidf"
    },
    "anomaly_detection_config": {
        "model_type": "isolation_forest"
    }
})

# Run LogAI
anomaly_detector = LogAnomalyDetection(config)
anomaly_detector.execute()
print(anomaly_detector.timestamps.columns)
results = anomaly_detector.results

# Send to Elasticsearch
send_to_elasticsearch("logai-results", results)

print(f"✅ Sent {len(results)} log entries to Elasticsearch.") 