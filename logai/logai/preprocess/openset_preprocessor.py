
from .preprocessor import Preprocessor, PreprocessorConfig
import pandas as pd
import re
from logai.dataloader.data_model import LogRecordObject
from logai.utils import constants

class OpenSetPreprocessor(Preprocessor):
    
    def __init__(self, config: PreprocessorConfig):
        super().__init__(config)
        self.config = config

    def _get_ids(self, logrecord: LogRecordObject) -> pd.Series:
        return None

    def _get_labels(self, logrecord: LogRecordObject) -> pd.Series:
        return None

    def _format_ids(self, data_id: pd.Series):
        if type(list(data_id)[0]) == str:
            id_to_serial_id_map = {k: i for i, k in enumerate(set(data_id))}
            data_id = data_id.apply(lambda x: id_to_serial_id_map[x])
        return data_id

    def clean_log(self, logrecord: LogRecordObject) -> LogRecordObject:
        
        preprocessed_loglines, custom_patterns = super().clean_log(
            logrecord.body[constants.LOGLINE_NAME]
        )
        for pattern in self.config.custom_replace_list:
            pattern = pattern[1]
            regex = r"((" + pattern + ")[ /=]*)+"
            value = pattern
            preprocessed_loglines = preprocessed_loglines.replace(
                to_replace=regex, value=value, regex=True
            )
        preprocessed_loglines = preprocessed_loglines.apply(
            lambda x: re.sub(" +", " ", x.replace("*", ""))
        )

        logrecord.body = pd.DataFrame({constants.LOGLINE_NAME: preprocessed_loglines})
        logrecord.body = logrecord.body.join(pd.DataFrame(custom_patterns))
        preprocessed_ids = self._get_ids(logrecord)
        preprocessed_ids = self._format_ids(preprocessed_ids)

        logrecord.span_id = pd.DataFrame({constants.SPAN_ID: preprocessed_ids})
        logrecord.labels = pd.DataFrame({constants.LABELS: self._get_labels(logrecord)})
        return logrecord
