
import logging

import pandas as pd

from logai.applications.application_interfaces import WorkFlowConfig
from logai.dataloader.data_loader import FileDataLoader
from logai.dataloader.data_model import LogRecordObject
from logai.dataloader.openset_data_loader import OpenSetDataLoader
from logai.information_extraction.log_parser import LogParser
from logai.preprocess.preprocessor import Preprocessor
from logai.utils import constants

class AutoLogSummarization:
    
    def __init__(self, config: WorkFlowConfig):
        
        self.config = config
        self._parsing_results = pd.DataFrame()
        self._attributes = None
        self._timestamp = None
        pass

    @property
    def parsing_results(self):
        return self._parsing_results

    @property
    def attributes(self):
        return self._attributes

    @property
    def log_patterns(self):
        if self._parsing_results.empty:
            return None
        return self._parsing_results[constants.PARSED_LOGLINE_NAME].unique()

    def get_parameter_list(self, log_pattern):
        
        para_list = pd.DataFrame(None, columns=["position", "value_counts", "values"])
        if self._parsing_results.empty or not log_pattern:
            return para_list

        res = self._parsing_results
        parameters = res.loc[res[constants.PARSED_LOGLINE_NAME] == log_pattern][
            constants.PARAMETER_LIST_NAME
        ]

        para_list["values"] = pd.Series(
            pd.DataFrame(parameters.tolist()).T.values.tolist()
        )
        para_list["position"] = [
            "POSITION_{}".format(v) for v in para_list.index.values
        ]
        para_list["value_counts"] = [
            len(list(filter(None, v))) for v in para_list["values"]
        ]
        return para_list

    def recognize_parameter_entity(self, para_list):
        
        pass

    def summarize_numeric_paramters(self, paras: list):
        
        pass

    def find_log_pattern(self, logline: str, return_para_list: bool = True):
        
        log_pattern = None
        para_list = None
        if not self._parsing_results.empty:
            res = self._parsing_results.loc[
                self._parsing_results[constants.LOGLINE_NAME] == logline
            ]
            log_patterns = res[constants.PARSED_LOGLINE_NAME]
            if len(log_patterns) == 0:
                return None
            if len(log_patterns) == 1:
                log_pattern_index = log_patterns.index[0]
                log_pattern = log_patterns.iloc[log_pattern_index]
            else:
                logging.warning("multiple log pa†terns are found!")
                log_pattern_index = log_patterns.index[0]
                log_pattern = log_patterns.iloc[log_pattern_index]
            if return_para_list:
                para_list = self.get_parameter_list(log_pattern)

        return log_pattern, para_list

    def execute(self):
        
        logrecord = self._load_data()

        if not logrecord.attributes.empty:
            self._attributes = logrecord.attributes.astype(str)

        if not logrecord.timestamp.empty:
            self._timestamp = logrecord.timestamp

        preprocessed_loglines = self._preprocess(logrecord)

        parser = LogParser(self.config.log_parser_config)
        parsed_results = parser.parse(preprocessed_loglines.dropna())
        self._parsing_results = parsed_results[
            [constants.PARSED_LOGLINE_NAME, constants.PARAMETER_LIST_NAME]
        ]

        self._parsing_results = self._parsing_results.join(logrecord.body)

        if self._attributes is not None:
            self._parsing_results = self._parsing_results.join(self._attributes)

        if self._timestamp is not None:
            self._parsing_results = self._parsing_results.join(self._timestamp)

        return

    def _load_data(self):
        if self.config.open_set_data_loader_config is not None:
            dataloader = OpenSetDataLoader(self.config.open_set_data_loader_config)
            logrecord = dataloader.load_data()
        elif self.config.data_loader_config is not None:
            dataloader = FileDataLoader(self.config.data_loader_config)
            logrecord = dataloader.load_data()
        else:
            raise ValueError(
                "data_loader_config or open_set_data_loader_config is needed to load data."
            )
        return logrecord

    def _preprocess(self, logrecord: LogRecordObject):
        logline = logrecord.body[constants.LOGLINE_NAME]

        preprocessor = Preprocessor(self.config.preprocessor_config)
        preprocessed_loglines, _ = preprocessor.clean_log(logline)

        return preprocessed_loglines
