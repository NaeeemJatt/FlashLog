
import numpy as np
import pandas as pd
from attr import dataclass
from sklearn.cluster import Birch

from logai.algorithms.algo_interfaces import ClusteringAlgo
from logai.config_interfaces import Config
from logai.algorithms.factory import factory

@dataclass
class BirchParams(Config):
    
    branching_factor: int = 50
    n_clusters: int = None
    threshold: float = 1.5

@factory.register("clustering", "birch", BirchParams)
class BirchAlgo(ClusteringAlgo):
    
    def __init__(self, params: BirchParams):
        self.model = Birch(
            branching_factor=params.branching_factor,
            n_clusters=params.n_clusters,
            threshold=params.threshold,
        )

    def fit(self, log_features: pd.DataFrame):
        
        log_features = np.ascontiguousarray(log_features)
        self.model.partial_fit(log_features)

    def predict(self, log_features: pd.DataFrame) -> pd.Series:
        
        log_features_carray = np.ascontiguousarray(log_features)

        res = self.model.predict(log_features_carray)
        return pd.Series(res, index=log_features.index)
