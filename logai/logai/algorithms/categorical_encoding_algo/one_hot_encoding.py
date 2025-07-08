
import numpy as np
import pandas as pd
from sklearn.preprocessing import OneHotEncoder

from logai.algorithms.algo_interfaces import CategoricalEncodingAlgo
from logai.config_interfaces import Config

class OneHotEncodingParams(Config):
    
    categories: str = "auto"
    drop: object = None
    dtype: np.float64 = np.float64
    handle_unknown: str = "error"

class OneHotEncoding(CategoricalEncodingAlgo):
    
    def __init__(self, params: OneHotEncodingParams):
        self.model = OneHotEncoder(
            categories=params.categories,
            drop=params.drop,
            sparse=False,
            dtype=params.dtype,
            handle_unknown=params.handle_unknown,
        )

    def fit_transform(self, log_attributes: pd.DataFrame) -> pd.DataFrame:
        
        col_names = log_attributes.columns
        if len(col_names) == 1:
            res_col_name_prefix = col_names[0]
        else:
            res_col_name_prefix = "-".join(col_names)
        self.model.fit(log_attributes)
        res = pd.DataFrame(
            self.model.transform(log_attributes), index=log_attributes.index
        )
        res_col_names = ["{}-{}".format(res_col_name_prefix, c) for c in res.columns]
        res.columns = res_col_names
        return res
