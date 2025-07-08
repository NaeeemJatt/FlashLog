
import numpy as np
import pandas as pd
from attr import dataclass

from logai.algorithms.algo_interfaces import AnomalyDetectionAlgo
from logai.config_interfaces import Config
from logai.algorithms.factory import factory

def _compute_probs(data, n=10):
    h, e = np.histogram(data, n)
    p = h / np.linalg.norm(h, ord=1)
    return e, p

def _kl_divergence(p, q):
    p[p == 0] = 1e-20
    q[q == 0] = 1e-20
    return np.sum(p * np.log(p / q))

def _js_divergence(p, q):
    m = (1.0 / 2.0) * (p + q)
    return (1.0 / 2.0) * _kl_divergence(p, m) + (1.0 / 2.0) * _kl_divergence(q, m)

@dataclass
class DistributionDivergenceParams(Config):
    """Parameters for distribution divergence based anomaly detector.

    :param n_bins: The number of bins to use to discretize the continuous distribution into a discrete distribution
    :param type: A list of types of distribution divergences. The allowed types are Kullback–Leibler ("KL"), Jensen–Shannon
        ("JS"). It also allows a comma separated list of metrics like ("KL,JS" or "JS,KL").
    """
    n_bins: int = 100
    type: list = ["KL"]

@factory.register("detection", "distribution_divergence", DistributionDivergenceParams)
class DistributionDivergence(AnomalyDetectionAlgo):
    
    def __init__(self, params: DistributionDivergenceParams):
        self.n_bins = params.n_bins
        self.type = params.type
        if any([x not in ["KL", "JS", "KL,JS", "JS,KL"] for x in self.type]):
            raise Exception("Type of distribution divergence allowed are: KL, JS")
        self.train_sample = None

    def fit(self, log_features: pd.DataFrame):
        
        self.train_sample = np.array(log_features)

    def predict(self, log_features: pd.DataFrame) -> list:
        
        log_features = np.array(log_features)
        if type(self.n_bins) == int:
            _, n_bins = np.histogram(
                np.vstack([np.array(self.train_sample), log_features]), self.n_bins
            )
        else:
            n_bins = self.n_bins
        e, p = _compute_probs(self.train_sample, n=n_bins)
        _, q = _compute_probs(log_features, n=e)

        dist_divergence_scores = []
        if "KL" in self.type:
            kl = _kl_divergence(p, q)
            dist_divergence_scores.append(kl)
        if "JS" in self.type:
            js = _js_divergence(p, q)
            dist_divergence_scores.append(js)
        return dist_divergence_scores
