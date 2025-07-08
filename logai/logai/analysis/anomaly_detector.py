
import pandas as pd
import logai.algorithms.anomaly_detection_algo

from attr import dataclass
from logai.config_interfaces import Config
from logai.algorithms.factory import factory

@dataclass
class AnomalyDetectionConfig(Config):
    
    algo_name: str = "one_class_svm"
    algo_params: object = None
    custom_params: object = None

    @classmethod
    def from_dict(cls, config_dict):
        config = super(AnomalyDetectionConfig, cls).from_dict(config_dict)
        config.algo_params = factory.get_config(
            "detection", config.algo_name.lower(), config.algo_params
        )
        return config

class AnomalyDetector:
    def __init__(self, config: AnomalyDetectionConfig):
        
        self.anomaly_detector = factory.get_algorithm(
            "detection", config.algo_name.lower(), config
        )

    def fit(self, log_features: pd.DataFrame):
        
        return self.anomaly_detector.fit(log_features)

    def predict(self, log_features: pd.DataFrame) -> pd.DataFrame:
        
        return self.anomaly_detector.predict(log_features)
