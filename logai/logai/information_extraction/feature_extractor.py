
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "logai")))

import numpy as np
import pandas as pd
from dataclasses import dataclass, fields, _MISSING_TYPE

from logai.config_interfaces import Config
from logai.utils import constants
from logai.utils.functions import pad
from typing import Union

@dataclass
class FeatureExtractorConfig(Config):
    
    group_by_category: list = None
    group_by_time: str = None
    sliding_window: int = 0
    steps: int = 1
    max_feature_len: int = 100

    def __post_init__(self):

        for field in fields(self):

            if (
                not isinstance(field.default, _MISSING_TYPE)
                and getattr(self, field.name) is None
            ):
                setattr(self, field.name, field.default)

def _get_group_counter(attributes: pd.DataFrame, group_by_category: list) -> pd.Series:
    
    attributes["group_index"] = attributes.index
    group_counter_list = (
        attributes.groupby(by=group_by_category)
        .size()
        .rename(constants.LOG_COUNTS)
        .reset_index()
    )
    return group_counter_list

class FeatureExtractor:
    
    def __init__(self, config: FeatureExtractorConfig):
        self.config = config

    def convert_to_counter_vector(
        self,
        log_pattern: pd.Series = None,
        attributes: pd.DataFrame = None,
        timestamps: pd.Series = None,
    ) -> pd.DataFrame:
        
        input_df = self._get_input_df(log_pattern, attributes, timestamps)

        gb = self._get_group(input_df)

        event_index_list = self._get_group_index(gb)
        event_index_list[constants.LOG_COUNTS] = event_index_list["event_index"].apply(
            lambda x: len(x) if hasattr(x, '__len__') else 1
        )

        return event_index_list

    def convert_to_feature_vector(
        self,
        log_vectors: pd.Series,
        attributes: pd.DataFrame,
        timestamps: pd.Series,
    ) -> pd.DataFrame:
        """
        Converts log data into feature vector, by combining the log vectors (can be output
        of LogVectorizer) with other numerical or categorical attributes of the logs,
        after grouping based on the FeatureExtractorConfig.
        
        :param log_vectors: Numeric features of the logs (for e.g. the vectorized form of the log data obtained as output of LogVectorizer).
        :param attributes: Categorical or numerical attributes for grouping, or numerical attributes serve as additional features.
        :param timestamps: pd.Series object containing the timestamp data of the loglines.

        :return: ``event_index_list``: modified log data (pd.DataFrame) consisting of the converted feature vector form of the input log data
            after applying the log grouping. It contains an "event_index" field which maintains the sequence of
            log event ids where these ids correspond to the  original input dataframe's indices.
            ``block_list``: pd.DataFrame object.
        """
        if log_vectors is None or log_vectors.empty:
            feature_df = None
        else:
            feature_df = self._convert_to_feature_df(log_vectors)
        input_df = self._get_input_df(feature_df, attributes, timestamps)

        gb = self._get_group(input_df)

        numeric_cols = input_df.select_dtypes(include=[np.number]).columns

        numeric_cols = input_df.select_dtypes(include=[np.number]).columns

        block_list = gb[numeric_cols].mean()

        for col in block_list.index.names:
            if col in block_list.columns:
                block_list = block_list.drop(columns=col)

        block_list = block_list.reset_index()

        event_index_list = gb.agg(list).reset_index()

        return event_index_list, block_list.loc[:, block_list.columns != "event_index"]

    def convert_to_sequence(
        self,
        log_pattern: pd.Series = None,
        attributes: pd.DataFrame = None,
        timestamps: pd.Series = None,
    ):
        """Converts log data into sequence using sliding window technique, as defined in FeatureExtractorConfig.
        
        :param log_pattern: A pd.Series object that encapsulates the entire arbitrary unstructured part of the log data
            (for example, can be the unstructured part of the raw log data or the output of the output of the log parser).
        :param attributes: The structured part (attributes) of the raw log data.
        :param timestamps: The timestamps data corresponding to the log lines.
        :return: ``event_index_list``: pd.DataFrame object of modified log data consisting of the sequence form of the
            structured and unstructured input data (i.e. log_pattern and attributes arguments) after running sliding
            window. For the unstructured part, the returned DataFrame contains an "event_index" field which maintains
            the sequence of log event ids where these ids correspond to the original input dataframe's indices.
            ``event_sequence``: pd.Series object containing the concatenating form of the unstructured input data
            (i.e. log_pattern argument), after concatenating the unstructured data for each sliding window.
        """

        input_df = self._get_input_df(log_pattern, attributes, timestamps)

        gb = self._get_group(input_df)

        if self.config.sliding_window > 0:
            if self.config.steps <= 0:
                raise RuntimeError(
                    "Step should be greater than zero. Step: {}".format(
                        self.config.steps
                    )
                )
            window = self.config.sliding_window
            step = self.config.steps
            raw_index_list = gb.agg(list).reset_index()
            colnames = raw_index_list.columns

            event_index_list = pd.DataFrame(columns=colnames)
            for ind, row in raw_index_list.iterrows():
                indices = row["event_index"]
                loglines = row[log_pattern.name]
                if len(indices) < self.config.sliding_window:
                    event_index_list = event_index_list.append(row)
                else:
                    event_indices = np.lib.stride_tricks.sliding_window_view(
                        indices, window
                    )[::step, :].tolist()
                    log_seq = np.lib.stride_tricks.sliding_window_view(
                        loglines, window
                    )[::step, :].tolist()

                    if (not timestamps.empty) and (not self.config.group_by_time):
                        ts = row[constants.LOG_TIMESTAMPS]
                        event_ts = np.lib.stride_tricks.sliding_window_view(ts, window)[
                            ::step, :
                        ].tolist()
                    for i in range(len(event_indices)):
                        row["event_index"] = event_indices[i]
                        row[log_pattern.name] = log_seq[i]
                        if (not timestamps.empty) and (not self.config.group_by_time):
                            row[constants.LOG_TIMESTAMPS] = event_ts[i]
                        event_index_list = event_index_list.append(row)
            event_sequence = event_index_list[log_pattern.name].apply(
                lambda x: " ".join(x)
            )

        else:
            event_index_list = gb.agg(list).reset_index()
            event_sequence = event_index_list["event_index"].apply(
                lambda x: " ".join([str(log_pattern[c]) for c in x])
            )

        return event_index_list, event_sequence

    def _get_input_df(
        self,
        logline: Union[pd.Series, pd.DataFrame],
        attributes: pd.DataFrame,
        timestamps: pd.Series,
    ) -> pd.DataFrame:
        if timestamps is not None:
            timestamps = timestamps.rename(constants.LOG_TIMESTAMPS)

        if logline is None:
            input_df = pd.concat((attributes, timestamps), axis=1)
        else:
            input_df = pd.concat((logline, attributes, timestamps), axis=1)
        input_df["event_index"] = input_df.index.values

        return input_df

    def _get_group_index(self, gb) -> pd.Series:
        event_index_list = gb.agg(list).reset_index()

        return event_index_list

    def _get_group_size(self, event_index_list) -> pd.Series:

        size_list = event_index_list["event_index_list"].apply(lambda x: len(x))
        return size_list

    def _get_deterministic_group(self, input_df):
        
        if 'logline' in input_df.columns:
            input_df['content_hash'] = input_df['logline'].apply(lambda x: hash(str(x)))
            return input_df.groupby('content_hash')
        else:

            return self._get_group(input_df)

    def _get_group(self, input_df):
        group_by = []
        if self.config.group_by_category:
            group_by += self.config.group_by_category

        if self.config.group_by_time:
            input_df[constants.LOG_TIMESTAMPS] = input_df[
                constants.LOG_TIMESTAMPS
            ].dt.floor(freq=self.config.group_by_time)
            group_by += [constants.LOG_TIMESTAMPS]
        if group_by:
            return input_df.groupby(by=group_by)
        else:
            return input_df.groupby(by=["event_index"])

    def _convert_to_feature_df(self, log_vectors: pd.Series) -> pd.DataFrame:
        padded_log_vectors = log_vectors.apply(pad, max_len=self.config.max_feature_len)
        log_features = pd.DataFrame(
            padded_log_vectors.tolist(), index=log_vectors.index
        )
        log_features.columns = [
            "feature_{}".format(i) for i in range(len(log_features.columns))
        ]
        return log_features