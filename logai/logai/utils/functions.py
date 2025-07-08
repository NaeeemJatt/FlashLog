
import numpy as np
import pandas as pd
from merlion.utils import TimeSeries

from logai.utils import constants

def pad(x, max_len: np.array, padding_value: int = 0):
    
    flattened_vector = x
    fill_size = max_len - len(flattened_vector)
    if fill_size > 0:
        fill_zeros = np.full(fill_size, fill_value=padding_value)
        return np.concatenate((flattened_vector, fill_zeros), axis=0)
    else:
        return flattened_vector[:max_len]

def get_parameter_list(row):
    parameter_list = []
    if not isinstance(row[constants.LOGLINE_NAME], str) or not isinstance(
        row[constants.PARSED_LOGLINE_NAME], str
    ):
        return parameter_list
    ll = row[constants.LOGLINE_NAME].split()
    pp = row[constants.PARSED_LOGLINE_NAME].split()
    buffer = []

    i = 0
    j = 0
    consec_pattern = False
    while i < len(ll) and j < len(pp):

        if ll[i] == pp[j]:
            if buffer:
                parameter_list.append(" ".join(buffer))
                buffer = []
            consec_pattern = False
            i += 1
            j += 1
        elif pp[j] == "*":
            if consec_pattern:
                parameter_list.append(" ".join(buffer))
                buffer = [ll[i]]
            else:
                buffer.append(ll[i])
            consec_pattern = True
            i += 1
            j += 1
        else:
            buffer.append(ll[i])
            i += 1
    if buffer:
        if i < len(ll):
            parameter_list.append(" ".join(buffer + ll[i:]))
        else:
            parameter_list.append(" ".join(buffer))
    return parameter_list

def pd_to_timeseries(log_features):
    
    if isinstance(log_features, pd.DataFrame):
        ts_df = log_features[constants.LOG_COUNTS]
        ts_df.index = log_features[constants.LOG_TIMESTAMPS]
    elif isinstance(log_features, pd.Series):

        ts_df = log_features
    else:
        raise ValueError(f"Expected DataFrame or Series, got {type(log_features)}")
    
    time_series = TimeSeries.from_pd(ts_df)
    return time_series
