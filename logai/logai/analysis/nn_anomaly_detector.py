
from datasets import Dataset as HFDataset
from logai.algorithms.vectorization_algo.forecast_nn import ForecastNNVectorizedDataset
from logai.analysis.anomaly_detector import AnomalyDetectionConfig
from logai.algorithms.factory import factory

NNAnomalyDetectionConfig = AnomalyDetectionConfig

class NNAnomalyDetector:
    def __init__(self, config: NNAnomalyDetectionConfig):
        
        self.anomaly_detector = factory.get_algorithm(
            "detection", config.algo_name.lower(), config
        )

    def fit(
        self,
        train_data: ForecastNNVectorizedDataset or HFDataset,
        dev_data: ForecastNNVectorizedDataset or HFDataset,
    ):
        
        return self.anomaly_detector.fit(train_data, dev_data)

    def predict(self, test_data: ForecastNNVectorizedDataset or HFDataset):
        
        return self.anomaly_detector.predict(test_data)
