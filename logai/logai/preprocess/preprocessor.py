
import numpy as np
import pandas as pd
from attr import dataclass

from logai.config_interfaces import Config
from logai.dataloader.data_model import LogRecordObject

@dataclass
class PreprocessorConfig(Config):
    
    custom_delimiters_regex: dict = None
    custom_replace_list: list = None

class Preprocessor:
    
    def __init__(self, config: PreprocessorConfig):
        self.config = config

    def clean_log(self, loglines: pd.Series) -> pd.Series:
        
        cleaned_log = loglines
        terms = pd.DataFrame()
        if self.config.custom_delimiters_regex:
            for reg in self.config.custom_delimiters_regex:
                try:
                    cleaned_log = cleaned_log.replace(
                        to_replace=reg, value=" ", regex=True
                    )
                except:
                    raise RuntimeError(
                        "Cannot replace custom regex delimiter {}".format(reg)
                    )

        if self.config.custom_replace_list:
            for pair in self.config.custom_replace_list:

                try:
                    pattern = pair[0]
                    replacement = pair[1]
                    terms[replacement] = cleaned_log.str.findall(pat=pattern)
                    cleaned_log = cleaned_log.replace(
                        to_replace=pattern, value=replacement, regex=True
                    )
                except:
                    raise RuntimeError(
                        "Cannot replace custom regex: {} values: {}".format(
                            pair[0], pair[1]
                        )
                    )
        return cleaned_log, terms

    def group_log_index(self, attributes: pd.DataFrame, by: np.array) -> pd.DataFrame:
        
        attributes["group_index"] = attributes.index
        group_index_list = (
            attributes.groupby(by=by).group_index.apply(np.array).reset_index()
        )

        return group_index_list

    def identify_timestamps(self, logrecord: LogRecordObject):
        pass
