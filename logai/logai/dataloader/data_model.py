
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
import pathlib
import json
from logai.utils import constants
import logging

@dataclass
class LogRecordObject:
    
    timestamp: pd.DataFrame = pd.DataFrame()
    attributes: pd.DataFrame = pd.DataFrame()
    resource: pd.DataFrame = pd.DataFrame()
    trace_id: pd.DataFrame = pd.DataFrame()
    span_id: pd.DataFrame = pd.DataFrame()
    severity_text: pd.DataFrame = pd.DataFrame()
    severity_number: pd.DataFrame = pd.DataFrame()
    body: pd.DataFrame = pd.DataFrame()
    labels: pd.DataFrame = pd.DataFrame()
    _index: np.array = field(init=False)

    def __post_init__(self):
        self._index = pd.DataFrame(self.body.index.values)

        for field in self.__dataclass_fields__:
            field_content = getattr(self, field)
            if not field_content.empty:
                if not field_content.index.equals(self._index.index):
                    raise IndexError(
                        "Index of {} should match Index of this object".format(field)
                    )

    def _meta_data(self):
        meta_data_dict = {}
        for field in self.__dataclass_fields__:
            field_content = getattr(self, field)
            if field == "_index":
                continue
            if type(field_content) == pd.DataFrame and not field_content.empty:
                columns = list(field_content.keys())
                meta_data_dict[field] = columns
        return meta_data_dict

    def to_dataframe(self):
        
        if self.body.empty:
            return None
        df = self.body
        for field in self.__dataclass_fields__:
            if field == "body":
                continue
            field_content = getattr(self, field)
            if not field_content.empty:
                df = df.join(field_content)

        return df

    @classmethod
    def from_dataframe(cls, data: pd.DataFrame, meta_data: dict = None):
        
        if meta_data is None and not data.empty:
            logbody = data.apply(" ".join, axis=1)
            return LogRecordObject(body=logbody)

        logrecord = LogRecordObject()
        for key, value in meta_data.items():
            if key not in logrecord.__dataclass_fields__.keys():
                raise KeyError(
                    "{} is not a field in LogRecordObject. The valid fields: {}".format(
                        key, logrecord.__dataclass_fields__.keys()
                    )
                )
            logrecord.__setattr__(key, data[value])
        logrecord.__post_init__()
        return logrecord

    def save_to_csv(self, filepath: str):
        
        f = pathlib.Path(filepath)
        filepath_metadata = filepath.replace(f.suffix, "_metadata.json")
        if f.suffix == ".csv":
            self.to_dataframe().to_csv(filepath, encoding="utf8")
        else:
            raise Exception("Only supports csv format")
        with open(filepath_metadata, "w") as fp:
            json.dump(self._meta_data(), fp)

    @classmethod
    def load_from_csv(cls, filepath):
        f = pathlib.Path(filepath)
        filepath_metadata = filepath.replace(f.suffix, "_metadata.json")
        data = pd.read_csv(filepath)
        meta_data = json.load(open(filepath_metadata))
        return cls.from_dataframe(data=data, meta_data=meta_data)

    def select_by_index(self, indices: list, inplace: bool = False):
        
        if not inplace:
            target = LogRecordObject()
        else:
            target = self
        for key in self.__dataclass_fields__.keys():
            val = getattr(self, key)
            if type(val) == pd.DataFrame and not val.empty:
                val = val[val.index.isin(indices)]
            target.__setattr__(key, val)
        return target

    def filter_by_index(self, indices: list, inplace: bool = False):
        
        if not inplace:
            target = LogRecordObject()
        else:
            target = self
        for key in self.__dataclass_fields__.keys():
            val = getattr(self, key)
            if type(val) == pd.DataFrame and not val.empty:
                val = val[~val.index.isin(indices)]
            target.__setattr__(key, val)
        return target

    def dropna(self):
        
        null_body = self.body.isnull()
        null_body = null_body[null_body[constants.LOGLINE_NAME] == True]
        null_indices = list(null_body.index)
        if len(null_indices) > 0:
            logging.info(
                "Removed {} indices with null value ".format(len(null_indices))
            )
            return self.filter_by_index(null_indices, inplace=True)
        else:
            return self
