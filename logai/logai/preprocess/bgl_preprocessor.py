
from logai.preprocess.openset_preprocessor import OpenSetPreprocessor
from logai.preprocess.preprocessor import PreprocessorConfig
import pandas as pd
from logai.utils import constants
from logai.dataloader.data_model import LogRecordObject

class BGLPreprocessor(OpenSetPreprocessor):
    
    def __init__(self, config: PreprocessorConfig):
        super().__init__(config)

    def _get_ids(self, logrecord: LogRecordObject) -> pd.Series:
        
        time_unit_in_secs = 60
        ids = logrecord.span_id[constants.SPAN_ID].astype(int)
        start_time = ids[0]
        session_ids = ids.apply(lambda x: int((x - start_time) / time_unit_in_secs))
        return session_ids

    def _get_labels(self, logrecord: LogRecordObject):
        
        return logrecord.labels[constants.LABELS].apply(lambda x: int(x != "-"))
