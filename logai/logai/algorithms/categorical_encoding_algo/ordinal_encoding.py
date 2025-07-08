
import numpy as np
import pandas as pd
from attr import dataclass
from sklearn.preprocessing import OrdinalEncoder

from logai.algorithms.algo_interfaces import CategoricalEncodingAlgo
from logai.config_interfaces import Config

@dataclass
class OrdinalEncodingParams(Config):
    
    categories: str = "auto"
    dtype: np.float64 = np.float64
    handle_unknown: str = "error"
    unknown_value: object = None

class OrdinalEncoding(CategoricalEncodingAlgo):
    
    def __init__(self, params: OrdinalEncodingParams):
        self.model = OrdinalEncoder(
            categories=params.categories,
            dtype=params.dtype,
            handle_unknown=params.handle_unknown,
            unknown_value=params.unknown_value,
        )

    def fit_transform(self, log_attributes: pd.DataFrame) -> pd.DataFrame:
        
        self.model.fit(log_attributes)
        res_column_names = ["{}-categorical".format(c) for c in log_attributes.columns]
        res = pd.DataFrame(
            self.model.transform(log_attributes), index=log_attributes.index
        )
        res.columns = res_column_names
        return res
