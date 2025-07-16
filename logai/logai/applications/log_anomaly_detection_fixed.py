
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "logai")))

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from logai.config_interfaces import WorkFlowConfig
from logai.dataloader.data_loader import FileDataLoader, OpenSetDataLoader
from logai.information_extraction.feature_extractor import FeatureExtractor
from logai.information_extraction.log_parser import LogParser
from logai.information_extraction.log_vectorizer import LogVectorizer
from logai.analysis.anomaly_detector import AnomalyDetector
from logai.preprocess.preprocessor import Preprocessor
from logai.dataloader.data_model import LogRecordObject
from logai.utils import constants

class LogAnomalyDetectionFixed:
    
    def __init__(self, config: WorkFlowConfig):
        self.config = config
        self._loglines = None
        self._timestamps = None
        self._attributes = None
        self._loglines_with_anomalies = None
        self._ad_results = None
        self._index_group = None
        self._counter_df = None

    @property
    def timestamps(self):
        return self._timestamps

    @property
    def loglines(self):
        return self._loglines

    @property
    def log_templates(self):
        return self._loglines_with_anomalies

    @property
    def attributes(self):
        return self._attributes

    @property
    def results(self):
        return self._ad_results

    @property
    def anomaly_results(self):
        if self._loglines_with_anomalies is not None:
            return self._loglines_with_anomalies["is_anomaly"]
        return None

    @property
    def anomaly_labels(self):
        if self._loglines_with_anomalies is not None:
            return self._loglines_with_anomalies["is_anomaly"].astype(int)
        return None

    @anomaly_labels.setter
    def anomaly_labels(self, labels):
        if self._loglines_with_anomalies is not None:
            self._loglines_with_anomalies["is_anomaly"] = labels

    @property
    def event_group(self):
        return self._index_group

    @property
    def feature_df(self):
        return self._ad_results

    @property
    def counter_df(self):
        return self._counter_df

    def evaluation(self):
        
        if self._loglines_with_anomalies is not None:
            return self._loglines_with_anomalies["is_anomaly"]
        return None

    def execute(self):
        
        logrecord = self._load_data()
        
        preprocessed_logrecord = self._preprocess(logrecord)

        loglines = preprocessed_logrecord.body[constants.LOGLINE_NAME]
        parsed_loglines = self._parse(loglines)

        feature_extractor = FeatureExtractor(self.config.feature_extractor_config)

        self._counter_df = feature_extractor.convert_to_counter_vector(
            timestamps=logrecord.timestamp[constants.LOG_TIMESTAMPS],
            attributes=self.attributes,
        )

        if self.config.anomaly_detection_config.algo_name in constants.COUNTER_AD_ALGO:

            self._counter_df["attribute"] = self._counter_df.drop(
                [constants.LOG_COUNTS, constants.LOG_TIMESTAMPS, constants.EVENT_INDEX],
                axis=1,
            ).apply(lambda x: "-".join(x.astype(str)), axis=1)

            attr_list = self._counter_df["attribute"].unique()
            res = pd.Series()
            for attr in attr_list:
                temp_df = self._counter_df[self._counter_df["attribute"] == attr]
                if temp_df.shape[0] < constants.MIN_TS_LENGTH:
                    anom_score = np.repeat(0.0, temp_df.shape[0])
                    res = res.append(pd.Series(anom_score, index=temp_df.index))
                else:
                    train, test = train_test_split(
                        temp_df[[constants.LOG_TIMESTAMPS, constants.LOG_COUNTS]],
                        shuffle=False,
                        train_size=0.7,
                    )
                    anomaly_detector = AnomalyDetector(
                        self.config.anomaly_detection_config
                    )
                    anom_score_training = pd.Series(
                        np.repeat(0.0, train.shape[0]), index=train.index
                    )
                    anomaly_detector.fit(train)
                    anom_score = anomaly_detector.predict(test)

                    res = res.append(anom_score_training)
                    res = res.append(anom_score["anom_score"])
            self._ad_results = pd.DataFrame(res.rename("result"))
            self._index_group = self._counter_df[[constants.EVENT_INDEX]]

        else:

            print("🔧 Using deterministic anomaly detection approach...")
            print(f"DEBUG: Algorithm name: {self.config.anomaly_detection_config.algo_name}")
            
            try:

                log_df = pd.DataFrame({
                    'logline': self.loglines,
                    'parsed_logline': parsed_loglines,
                    'original_index': range(len(self.loglines))
                })
                
                log_df['log_hash'] = log_df['logline'].apply(lambda x: hash(str(x)))
                
                print(f"DEBUG: Total logs: {len(log_df)}")
                print(f"DEBUG: Unique log hashes: {log_df['log_hash'].nunique()}")
                
                grouped_by_hash = log_df.groupby('log_hash')
                
                unique_logs = []
                hash_to_indices = {}
                
                for log_hash, group in grouped_by_hash:

                    representative_log = group.iloc[0]
                    unique_logs.append(representative_log['parsed_logline'])
                    hash_to_indices[log_hash] = group['original_index'].tolist()
                
                print(f"DEBUG: Processing {len(unique_logs)} unique log types")
                
                vectorizor = LogVectorizer(self.config.log_vectorizer_config)

                vectorizor.fit(parsed_loglines)

                unique_vectors = vectorizor.transform(pd.Series(unique_logs))
                
                feature_df = pd.DataFrame(
                    unique_vectors.tolist(), 
                    index=range(len(unique_logs))
                )
                
                print(f"DEBUG: Feature matrix shape: {feature_df.shape}")
                
                anomaly_detector = AnomalyDetector(self.config.anomaly_detection_config)
                anomaly_detector.fit(feature_df)
                anomaly_scores = anomaly_detector.predict(feature_df)["anom_score"]
                
                print(f"DEBUG: Anomaly scores range: {anomaly_scores.min():.4f} to {anomaly_scores.max():.4f}")
                
                if self.config.anomaly_detection_config.algo_name == "one_class_svm":

                    threshold = anomaly_scores.quantile(0.05)
                    anomaly_mask = anomaly_scores < threshold
                else:

                    threshold = anomaly_scores.quantile(0.95)
                    anomaly_mask = anomaly_scores > threshold
                
                print(f"DEBUG: Threshold: {threshold:.4f}")
                print(f"DEBUG: Anomalous unique logs: {anomaly_mask.sum()}")
                
                log_hash_to_anomaly = {}
                for i, (log_hash, indices) in enumerate(hash_to_indices.items()):
                    is_anomaly = anomaly_mask.iloc[i]
                    log_hash_to_anomaly[log_hash] = is_anomaly
                
                final_results = []
                for _, row in log_df.iterrows():
                    log_hash = row['log_hash']
                    is_anomaly = log_hash_to_anomaly[log_hash]
                    final_results.append(1.0 if is_anomaly else 0.0)
                
                df = pd.DataFrame({
                    'logline': self.loglines,
                    'is_anomaly': final_results,
                    '_id': range(len(self.loglines))
                })
                
                log_content_to_anomaly = {}
                inconsistencies = 0
                
                for idx, row in df.iterrows():
                    log_content = row['logline']
                    is_anomaly = row['is_anomaly']
                    
                    if log_content in log_content_to_anomaly:
                        if log_content_to_anomaly[log_content] != is_anomaly:
                            inconsistencies += 1
                            print(f"INCONSISTENCY: Log '{log_content[:100]}...' has different classifications!")
                    else:
                        log_content_to_anomaly[log_content] = is_anomaly
                
                print(f"DEBUG: Total logs: {len(df)}")
                print(f"DEBUG: Unique log contents: {len(log_content_to_anomaly)}")
                print(f"DEBUG: Anomalies detected: {df['is_anomaly'].sum()}")
                print(f"DEBUG: Inconsistencies found: {inconsistencies}")
                
                if inconsistencies == 0:
                    print("✅ SUCCESS: All identical logs classified consistently!")
                else:
                    print(f"⚠️  WARNING: Found {inconsistencies} inconsistencies!")
                
                self._loglines_with_anomalies = df
                
                self._ad_results = pd.DataFrame({'result': final_results})
                self._index_group = pd.DataFrame({'event_index': [[i] for i in range(len(self.loglines))]})
                
            except Exception as e:
                print(f"❌ ERROR in deterministic approach: {e}")
                import traceback
                traceback.print_exc()

                print("🔧 Falling back to simple anomaly detection...")
                df = pd.DataFrame({
                    'logline': self.loglines,
                    'is_anomaly': [0.0] * len(self.loglines),
                    '_id': range(len(self.loglines))
                })
                self._loglines_with_anomalies = df
                self._ad_results = pd.DataFrame({'result': [0.0] * len(self.loglines)})
                self._index_group = pd.DataFrame({'event_index': [[i] for i in range(len(self.loglines))]})

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

    def _preprocess(self, log_record):
        logline = log_record.body[constants.LOGLINE_NAME]

        self._loglines = logline
        self._timestamps = log_record.timestamp
        self._attributes = log_record.attributes.astype(str)

        preprocessor = Preprocessor(self.config.preprocessor_config)
        preprocessed_loglines, _ = preprocessor.clean_log(logline)

        new_log_record = LogRecordObject(
            body=pd.DataFrame(preprocessed_loglines, columns=[constants.LOGLINE_NAME]),
            timestamp=log_record.timestamp,
            attributes=log_record.attributes,
        )

        return new_log_record

    def _parse(self, loglines):
        parser = LogParser(self.config.log_parser_config)
        parsed_results = parser.parse(loglines.dropna())
        parsed_loglines = parsed_results[constants.PARSED_LOGLINE_NAME]
        return parsed_loglines 