
import abc

import pandas as pd
from logai.dataloader.data_model import LogRecordObject

class ParsingAlgo(abc.ABC):
    
    @abc.abstractmethod
    def fit(self, loglines: pd.Series):
        pass

    @abc.abstractmethod
    def parse(self, loglines: pd.Series) -> pd.DataFrame:
        pass

class VectorizationAlgo(abc.ABC):
    
    @abc.abstractmethod
    def fit(self, loglines: pd.Series):
        pass

    @abc.abstractmethod
    def transform(self, loglines: pd.Series):
        pass

class FeatureExtractionAlgo(abc.ABC):
    
    @abc.abstractmethod
    def fit_transform(self, log_attributes: pd.DataFrame) -> pd.DataFrame:
        pass

class ClusteringAlgo(abc.ABC):
    
    @abc.abstractmethod
    def fit(self, log_attributes: pd.DataFrame):
        pass

    @abc.abstractmethod
    def predict(self, log_attributes: pd.DataFrame):
        pass

class CategoricalEncodingAlgo(abc.ABC):
    
    @abc.abstractmethod
    def fit_transform(self, log_attributes: pd.DataFrame) -> pd.DataFrame:
        pass

class AnomalyDetectionAlgo(abc.ABC):
    
    @abc.abstractmethod
    def fit(self, log_attributes: pd.DataFrame):
        pass

    @abc.abstractmethod
    def predict(self, log_attributes: pd.DataFrame):
        pass

class NNAnomalyDetectionAlgo(abc.ABC):
    
    @abc.abstractmethod
    def fit(self, log_attributes: pd.DataFrame):
        pass

    @abc.abstractmethod
    def predict(self, log_attributes: pd.DataFrame):
        pass
