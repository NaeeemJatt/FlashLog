
from logai.preprocess.openset_preprocessor import OpenSetPreprocessor
from logai.preprocess.preprocessor import PreprocessorConfig
import pandas as pd
from logai.utils import constants
from logai.dataloader.data_model import LogRecordObject

class HDFSPreprocessor(OpenSetPreprocessor):
    
    def __init__(self, config: PreprocessorConfig, label_file: str):
        super().__init__(config)
        self.id_separator = " "
        self.label_file = label_file

    def _get_labels(self, logrecord: LogRecordObject):
        
        blk_df = pd.read_csv(self.label_file, header=0)
        anomaly_blk = set(blk_df[blk_df["Label"] == "Anomaly"]["BlockId"])
        block_ids = logrecord.span_id[constants.SPAN_ID].apply(
            lambda x: set(
                self.serial_id_to_predefined_id_map[x].split(self.id_separator)
            )
        )
        labels = block_ids.apply(lambda x: int(len(x.intersection(anomaly_blk)) > 0))
        return labels

    def _get_ids(self, logrecord: LogRecordObject):
        
        predefined_ids = logrecord.body[" BLOCK "]
        predefined_ids = predefined_ids.apply(lambda x: self.id_separator.join(set(x)))
        self.predefined_to_serial_id_map = {
            k: i for i, k in enumerate(list(predefined_ids))
        }
        self.serial_id_to_predefined_id_map = {
            v: k for k, v in self.predefined_to_serial_id_map.items()
        }
        predefined_ids = predefined_ids.apply(
            lambda x: self.predefined_to_serial_id_map[x]
        ).astype(int)
        return predefined_ids
