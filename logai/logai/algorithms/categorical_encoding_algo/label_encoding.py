
import pandas as pd
from sklearn.preprocessing import LabelEncoder

from logai.algorithms.algo_interfaces import CategoricalEncodingAlgo

class LabelEncoding(CategoricalEncodingAlgo):
    
    def __init__(self):
        
        self.model = LabelEncoder()

    def fit_transform(self, log_attributes: pd.DataFrame):
        
        res = pd.DataFrame()
        for feature_name in log_attributes.columns:
            x = self.model.fit_transform(log_attributes[feature_name])
            x_name = "{}_categorical".format(feature_name)
            res[x_name] = pd.Series(x, index=log_attributes[feature_name].index)
        return res
