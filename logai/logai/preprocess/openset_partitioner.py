
from .partitioner import Partitioner, PartitionerConfig
from logai.information_extraction.feature_extractor import (
    FeatureExtractor,
    FeatureExtractorConfig,
)
import pandas as pd
from logai.utils import constants
from logai.config_interfaces import Config

from attr import dataclass

@dataclass
class OpenSetPartitionerConfig(Config):
    
    sliding_window: int = 0
    session_window: bool = True
    logsequence_delim: str = "[SEP]"

class OpenSetPartitioner:
    
    def __init__(self, config: OpenSetPartitionerConfig):
        
        self.config = config

        if config.sliding_window > 0:
            partitioner_config = PartitionerConfig.from_dict(
                {
                    "sliding_window": config.sliding_window,
                    "sep_token": config.logsequence_delim,
                    "group_by_category": [constants.SPAN_ID],
                    "exclude_last_window": True,
                    "exclude_smaller_windows": True,
                }
            )
            self.partitioner = Partitioner(partitioner_config)
        elif config.session_window:
            fe_config = FeatureExtractorConfig.from_dict(
                {
                    "sliding_window": 20,
                    "steps": 20,
                    "group_by_category": [constants.SPAN_ID],
                }
            )
            self.feature_extractor = FeatureExtractor(fe_config)

    def _get_group_sliding_window(
        self, logrecord_df, logline_col_name=constants.LOGLINE_NAME
    ):
        logrecord_df[logline_col_name] = logrecord_df[logline_col_name].astype(str)
        return self.partitioner.group_sliding_window(logrecord_df, logline_col_name)

    def _get_sliding_window_label(self, log_data):
        partitioned_data = self._get_group_sliding_window(
            log_data, logline_col_name=constants.LABELS
        )
        partitioned_labels = partitioned_data[constants.LABELS].apply(
            lambda x: int("1" in x)
        )
        partitioned_labels_nextdata = self._get_next_data_succeeding_sliding_window(
            log_data, partitioned_data, constants.LABELS
        ).astype(int)
        partitioned_labels = (
            (partitioned_labels_nextdata + partitioned_labels) > 0
        ).astype(int)
        return partitioned_labels

    def _get_next_data_succeeding_sliding_window(self, data, sliding_windows, field):
        data_groupbyid = {
            k: list(v) for k, v in data.groupby(by=[constants.SPAN_ID])[field]
        }
        nextdata = []
        for id, groupdata in sliding_windows.groupby(by=[constants.SPAN_ID])[field]:
            nextdata.extend(data_groupbyid[id][-len(groupdata) :])
        nextdata = pd.Series(nextdata).astype(data[field].dtype)
        return nextdata

    def generate_sliding_window(self, logrecord):
        
        log_data = logrecord.to_dataframe()
        partitioned_data = self._get_group_sliding_window(
            log_data, logline_col_name=constants.LOGLINE_NAME
        )
        partitioned_nextdata = self._get_next_data_succeeding_sliding_window(
            log_data, partitioned_data, constants.LOGLINE_NAME
        )
        partitioned_labels = self._get_sliding_window_label(log_data)
        partitioned_ids = partitioned_data[constants.SPAN_ID]
        partitioned_loglines = partitioned_data[constants.LOGLINE_NAME]
        logrecord.body = pd.DataFrame({constants.LOGLINE_NAME: partitioned_loglines})
        logrecord.attributes = pd.DataFrame(
            {constants.NEXT_LOGLINE_NAME: partitioned_nextdata}
        )
        logrecord.labels = pd.DataFrame({constants.LABELS: partitioned_labels})
        logrecord.span_id = pd.DataFrame({constants.SPAN_ID: partitioned_ids})
        return logrecord

    def generate_session_window(self, logrecord):
        
        partitioned_data = self.feature_extractor.convert_to_counter_vector(
            log_pattern=logrecord.body[constants.LOGLINE_NAME],
            attributes=logrecord.span_id.join(logrecord.labels),
            timestamps=logrecord.timestamp[constants.LOG_TIMESTAMPS],
        )
        partitioned_loglines = partitioned_data[constants.LOGLINE_NAME].apply(
            lambda x: self.config.logsequence_delim.join(x)
        )
        partitioned_labels = partitioned_data[constants.LABELS].apply(
            lambda x: int(sum(x) > 0)
        )
        partitioned_ids = partitioned_data[constants.SPAN_ID]
        logrecord.body = pd.DataFrame({constants.LOGLINE_NAME: partitioned_loglines})
        logrecord.labels = pd.DataFrame({constants.LABELS: partitioned_labels})
        logrecord.span_id = pd.DataFrame({constants.SPAN_ID: partitioned_ids})
        return logrecord

    def partition(self, logrecord):
        
        if self.config.sliding_window > 0:
            logrecord = self.generate_sliding_window(logrecord)
        elif self.config.session_window:
            logrecord = self.generate_session_window(logrecord)
        return logrecord
