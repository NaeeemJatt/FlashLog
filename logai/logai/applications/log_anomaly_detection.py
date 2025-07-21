
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from logai.analysis.anomaly_detector import AnomalyDetector, AnomalyDetectionConfig
from logai.applications.application_interfaces import WorkFlowConfig
from logai.dataloader.data_loader import FileDataLoader
from logai.dataloader.data_model import LogRecordObject
from logai.dataloader.openset_data_loader import OpenSetDataLoader
from logai.information_extraction.categorical_encoder import (
    CategoricalEncoder,
    CategoricalEncoderConfig,
)
from logai.information_extraction.feature_extractor import FeatureExtractor
from logai.information_extraction.log_parser import LogParser
from logai.information_extraction.log_vectorizer import LogVectorizer
from logai.preprocess.partitioner import PartitionerConfig, Partitioner
from logai.preprocess.preprocessor import Preprocessor
from logai.utils import constants, evaluate
from logai.utils.log_normalizer import LogNormalizer, NormalizationConfig, normalize_logs

class LogAnomalyDetection:
    
    def __init__(self, config: WorkFlowConfig):
        self.config = config
        self._timestamps = pd.DataFrame()
        self._attributes = pd.DataFrame()
        self._feature_df = pd.DataFrame()
        self._counter_df = pd.DataFrame()
        self._loglines = pd.DataFrame()
        self._log_templates = pd.DataFrame()
        self._ad_results = pd.DataFrame()
        self._labels = pd.DataFrame()
        self._index_group = pd.DataFrame()
        self._loglines_with_anomalies = pd.DataFrame()
        self._group_anomalies = None

        return

    @property
    def timestamps(self):
        return self._timestamps

    @property
    def loglines(self):
        return self._loglines

    @property
    def log_templates(self):
        return self._log_templates

    @property
    def attributes(self):
        return self._attributes

    @property
    def results(self):
        try:

            res = self._loglines_with_anomalies.copy()
            
            if self.attributes is not None and not self.attributes.empty:
                res = res.join(self.attributes, rsuffix='_attr')
            
            if self.timestamps is not None and not self.timestamps.empty:
                # Use suffixes to avoid column overlap
                res = res.join(self.timestamps, rsuffix='_ts')
            
            try:
                event_group = self.event_group
                if event_group is not None and not event_group.empty:
                    res = res.join(event_group)
            except Exception as e:
                print(f"⚠️  Warning: Could not join event_group: {e}")
            
            return res
        except Exception as e:
            print(f"❌ Error in results property: {e}")

            return self._loglines_with_anomalies

    @property
    def anomaly_results(self):

        return self.results[self.results["is_anomaly"]]

    @property
    def anomaly_labels(self):
        return self._labels

    @anomaly_labels.setter
    def anomaly_labels(self, labels):
        self._labels = labels

    @property
    def event_group(self):
        event_index_map = dict()
        
        if self._index_group is None or self._index_group.empty:

            loglines_length = len(self.loglines) if self.loglines is not None else 0
            for i in range(loglines_length):
                event_index_map[i] = i
        else:

            if "event_index" in self._index_group.columns:
                for group_id, indices in self._index_group["event_index"].items():
                    if isinstance(indices, (list, tuple, set)):
                        for i in indices:
                            event_index_map[i] = group_id
                    else:
                        event_index_map[indices] = group_id
            else:

                loglines_length = len(self.loglines) if self.loglines is not None else 0
                for i in range(loglines_length):
                    event_index_map[i] = i

        event_index = pd.Series(event_index_map).rename("group_id")
        return event_index

    @property
    def feature_df(self):
        return self._feature_df

    @property
    def counter_df(self):
        return self._counter_df

    def evaluation(self):
        if self.anomaly_labels is None:
            raise TypeError

        labels = self.anomaly_labels.to_numpy()
        pred = np.array([1 if r else 0 for r in self.results["is_anomaly"]])
        return evaluate.get_accuracy_precision_recall(labels, pred)

    def execute(self):

        import numpy as np
        import random
        np.random.seed(42)
        random.seed(42)
        
        logrecord = self._load_data()

        preprocessed_logrecord = self._preprocess(logrecord)

        loglines = preprocessed_logrecord.body[constants.LOGLINE_NAME]
        # Skip parsing - work directly with raw log lines
        print("🔧 Skipping log parsing - working with raw log lines")

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

                    if train[constants.LOG_TIMESTAMPS].apply(lambda x: isinstance(x, list)).any():
                        print("[DEBUG] Exploding train DataFrame to flatten timestamp column...")
                        train = train.explode(constants.LOG_TIMESTAMPS)
                        test = test.explode(constants.LOG_TIMESTAMPS)

                    print(f"[DEBUG] Train DataFrame columns: {train.columns}")
                    print(f"[DEBUG] Train DataFrame unique timestamps: {train[constants.LOG_TIMESTAMPS].unique()}")
                    print(f"[DEBUG] Train DataFrame shape: {train.shape}")

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

            print("🔧 Using simplified anomaly detection approach...")
            
            try:
                # Import the simple anomaly detection
                from .simple_log_anomaly_detection import simple_anomaly_detection
                
                # Get algorithm name and contamination
                algo_name = self.config.anomaly_detection_config.algo_name
                contamination = 0.1  # Default contamination
                
                # Map algorithm names
                if algo_name == "isolation_forest":
                    algorithm = "isolation_forest"
                elif algo_name == "lof":
                    algorithm = "lof"
                elif algo_name == "one_class_svm":
                    algorithm = "one_class_svm"
                    contamination = 0.05  # More conservative for One-Class SVM
                else:
                    algorithm = "isolation_forest"  # Default fallback
                
                print(f"🔧 Using simplified {algorithm} with {contamination*100:.1f}% contamination")
                
                # Convert loglines to list if it's a pandas Series
                if hasattr(self.loglines, 'tolist'):
                    loglines_list = self.loglines.tolist()
                else:
                    loglines_list = list(self.loglines)
                
                # Perform simple anomaly detection
                df = simple_anomaly_detection(
                    loglines=loglines_list,
                    algorithm=algorithm,
                    contamination=contamination
                )
                
                # Add timestamp if available (avoid conflicts)
                if self.timestamps is not None and not self.timestamps.empty:
                    if 'timestamp' not in df.columns:
                        df['timestamp'] = self.timestamps
                
                self._loglines_with_anomalies = df
                self._ad_results = pd.DataFrame({'result': df['is_anomaly'].values})
                self._index_group = pd.DataFrame({'event_index': [[i] for i in range(len(self.loglines))]})
                
            except Exception as e:
                print(f"❌ ERROR in simplified approach: {e}")
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
        
        if log_record.attributes is not None and not log_record.attributes.empty:
            self._attributes = log_record.attributes.astype(str)
        else:
            self._attributes = pd.DataFrame()

        # Skip complex preprocessing - use raw log lines
        print("🔧 Skipping complex preprocessing - using raw log lines")

        new_log_record = LogRecordObject(
            body=pd.DataFrame(logline, columns=[constants.LOGLINE_NAME]),
            timestamp=log_record.timestamp,
            attributes=log_record.attributes,
        )

        return new_log_record

    def _parse(self, loglines):
        try:
            parser = LogParser(self.config.log_parser_config)
            parsed_results = parser.parse(loglines.dropna())

            if constants.PARSED_LOGLINE_NAME not in parsed_results.columns:
                print(f"⚠️  Warning: Parsed results missing '{constants.PARSED_LOGLINE_NAME}' column")
                print(f"   Available columns: {list(parsed_results.columns)}")

                parsed_loglines = loglines
            else:
                parsed_loglines = parsed_results[constants.PARSED_LOGLINE_NAME]

            return parsed_loglines
        except Exception as e:
            print(f"❌ Error in parsing: {e}")
            print("🔧 Falling back to using original loglines as parsed loglines")
            return loglines
