
from logai.algorithms.algo_interfaces import NNAnomalyDetectionAlgo
from logai.algorithms.nn_model.logbert.configs import LogBERTConfig
from logai.algorithms.nn_model.logbert.train import LogBERTTrain
from logai.algorithms.nn_model.logbert.predict import LogBERTPredict
from logai.algorithms.factory import factory
from datasets import Dataset as HFDataset
import pandas as pd

@factory.register("detection", "logbert", LogBERTConfig)
class LogBERT(NNAnomalyDetectionAlgo):
    
    def __init__(self, config: LogBERTConfig):
        self.logbert_train = LogBERTTrain(config=config)
        self.logbert_predict = LogBERTPredict(config=config)

    def fit(self, train_data: HFDataset, dev_data: HFDataset):
        
        self.logbert_train.fit(train_data, dev_data)

    def predict(self, test_data: HFDataset) -> pd.DataFrame:
        
        return self.logbert_predict.predict(test_data)
