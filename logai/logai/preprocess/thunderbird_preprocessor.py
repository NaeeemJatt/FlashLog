
from logai.preprocess.openset_preprocessor import OpenSetPreprocessor
from logai.dataloader.data_model import LogRecordObject
from logai.preprocess.preprocessor import PreprocessorConfig
import pandas as pd
from logai.utils import constants

class ThunderbirdPreprocessor(OpenSetPreprocessor):
    
    def __init__(self, config: PreprocessorConfig):
        super().__init__(config)

    def _get_ids(self, logrecord: LogRecordObject) -> pd.Series:
        
        return logrecord.span_id[constants.SPAN_ID]

    def _get_labels(self, logrecord: LogRecordObject):
        
        return logrecord.labels[constants.LABELS].apply(lambda x: int(x != "-"))
