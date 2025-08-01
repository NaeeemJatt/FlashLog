
import pandas as pd
from attr import dataclass
from sklearn.neighbors import LocalOutlierFactor
import numpy as np

from logai.algorithms.algo_interfaces import AnomalyDetectionAlgo
from logai.config_interfaces import Config
from logai.algorithms.factory import factory

@dataclass
class LOFParams(Config):
    
    n_neighbors: int = 20
    algorithm: str = "auto"
    leaf_size: int = 30
    metric: callable or str = "minkowski"
    p: int = 2
    metric_params: dict = None
    contamination: str = "auto"
    novelty: bool = True
    n_jobs: int = None

@factory.register("detection", "lof", LOFParams)
class LOFDetector(AnomalyDetectionAlgo):
    
    def __init__(self, params: LOFParams):
        self.model = LocalOutlierFactor(
            n_neighbors=params.n_neighbors,
            algorithm=params.algorithm,
            leaf_size=params.leaf_size,
            metric=params.metric,
            p=params.p,
            metric_params=params.metric_params,
            contamination=params.contamination,
            novelty=params.novelty,
            n_jobs=params.n_jobs,
        )

    def fit(self, log_features: pd.DataFrame):
        
        self.model.fit(
            np.array(log_features)
        )
        train_scores = self.model.score_samples(log_features)
        train_scores = pd.DataFrame(train_scores, index=log_features.index)
        train_scores["trainval"] = True
        return train_scores

    def predict(self, log_features: pd.DataFrame) -> pd.Series:
        
        test_scores = self.model.predict(
            np.array(log_features)
        )
        test_scores = pd.DataFrame(
            pd.Series(test_scores, index=log_features.index, name="anom_score")
        )

        test_scores["trainval"] = False
        return test_scores
