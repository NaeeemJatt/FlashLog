
import pandas as pd
from attr import dataclass
from sklearn.cluster import DBSCAN

from logai.algorithms.algo_interfaces import ClusteringAlgo
from logai.config_interfaces import Config
from logai.algorithms.factory import factory

@dataclass
class DbScanParams(Config):
    
    eps: float = 0.3
    min_samples: int = 10
    metric: str = "euclidean"
    metric_params: object = None
    algorithm: str = "auto"
    leaf_size: int = 30
    p: float = None
    n_jobs: int = None

@factory.register("clustering", "dbscan", DbScanParams)
class DbScanAlgo(ClusteringAlgo):
    
    def __init__(self, params: DbScanParams):
        self.model = DBSCAN(
            eps=params.eps,
            min_samples=params.min_samples,
            metric=params.metric,
            metric_params=params.metric_params,
            algorithm=params.algorithm,
            leaf_size=params.leaf_size,
            p=params.p,
            n_jobs=params.n_jobs,
        )

    def fit(self, log_features: pd.DataFrame):
        
        self.model.fit(log_features)

    def predict(self, log_features: pd.DataFrame) -> pd.Series:
        
        res = self.model.fit_predict(log_features)
        return pd.Series(res, index=log_features.index)
