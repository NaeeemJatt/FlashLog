
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
                res = res.join(self.attributes)
            
            if self.timestamps is not None and not self.timestamps.empty:
                res = res.join(self.timestamps)
            
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

            print("🔧 Using deterministic anomaly detection approach...")
            
            try:

                log_df = pd.DataFrame({
                    'logline': self.loglines,
                    'parsed_logline': parsed_loglines,
                    'original_index': range(len(self.loglines))
                })
                
                normalizer_config = NormalizationConfig(
                    normalize_ips=True,
                    normalize_ports=True,
                    normalize_timestamps=True,
                    normalize_uuids=True,
                    normalize_hashes=True,
                    normalize_file_paths=True,
                    normalize_hex_values=True,
                    enable_caching=True,
                    cache_size=1000
                )
                normalizer = LogNormalizer(normalizer_config)
                
                normalized_loglines = normalizer.normalize_batch(log_df['logline'].tolist())
                log_df['normalized_logline'] = normalized_loglines
                
                log_df['log_hash'] = log_df['normalized_logline'].apply(lambda x: hash(str(x)))
                
                print(f"🔍 DEBUG: Total logs: {len(log_df)}")
                print(f"🔍 DEBUG: Unique normalized log patterns: {log_df['normalized_logline'].nunique()}")
                print(f"🔍 DEBUG: Unique log hashes: {log_df['log_hash'].nunique()}")
                
                print(f"🔍 DEBUG: Normalization examples:")
                for i, (original, normalized) in enumerate(zip(log_df['logline'].head(3), log_df['normalized_logline'].head(3))):
                    print(f"  Original {i+1}: {original[:80]}...")
                    print(f"  Normalized: {normalized[:80]}...")
                    print()
                
                grouped_by_hash = log_df.groupby('log_hash')
                
                unique_logs = []
                hash_to_indices = {}
                
                for log_hash, group in grouped_by_hash:

                    representative_log = group.iloc[0]
                    unique_logs.append(representative_log['parsed_logline'])
                    hash_to_indices[log_hash] = group['original_index'].tolist()
                
                print(f"🔍 DEBUG: Processing {len(unique_logs)} unique log types")
                
                vectorizor = LogVectorizer(self.config.log_vectorizer_config)

                vectorizor.fit(parsed_loglines)

                unique_vectors = vectorizor.transform(pd.Series(unique_logs))
                
                feature_df = pd.DataFrame(
                    unique_vectors.tolist(), 
                    index=range(len(unique_logs))
                )
                
                print(f"🔍 DEBUG: Feature matrix shape: {feature_df.shape}")
                
                anomaly_detector = AnomalyDetector(self.config.anomaly_detection_config)
                
                if self.config.anomaly_detection_config.algo_name == "one_class_svm":

                    try:
                        current_nu = self.config.anomaly_detection_config.algo_params.nu
                        if current_nu > 0.1:
                            print(f"⚠️  WARNING: One-Class SVM nu parameter is {current_nu} (expects {current_nu*100:.0f}% outliers)")
                            print("🔧 This is likely causing too many anomalies to be detected!")
                            print("🔧 Consider setting nu to 0.05-0.1 for typical log anomaly detection")
                    except:
                        print("⚠️  WARNING: Could not check One-Class SVM nu parameter")
                
                anomaly_detector.fit(feature_df)
                anomaly_scores = anomaly_detector.predict(feature_df)["anom_score"]
                
                print(f"🔍 DEBUG: Anomaly scores range: {anomaly_scores.min():.4f} to {anomaly_scores.max():.4f}")
                
                if self.config.anomaly_detection_config.algo_name == "one_class_svm":

                    threshold = anomaly_scores.quantile(0.05)
                    anomaly_mask = anomaly_scores <= threshold
                    print(f"🔍 DEBUG: One-Class SVM - Lower scores are anomalies")
                    print(f"🔍 DEBUG: Threshold (5th percentile): {threshold:.4f}")
                    print(f"🔍 DEBUG: Score range: {anomaly_scores.min():.4f} to {anomaly_scores.max():.4f}")
                    print(f"🔍 DEBUG: Scores at 5th percentile: {anomaly_scores.quantile(0.05):.4f}")
                    print(f"🔍 DEBUG: Scores at 10th percentile: {anomaly_scores.quantile(0.10):.4f}")
                    print(f"🔍 DEBUG: Scores at 25th percentile: {anomaly_scores.quantile(0.25):.4f}")
                    print(f"🔍 DEBUG: Scores at 50th percentile: {anomaly_scores.quantile(0.50):.4f}")
                    
                    if anomaly_scores.nunique() == 1:
                        print("⚠️  WARNING: All anomaly scores are identical! This suggests a model issue.")
                        print("🔧 Using a more conservative threshold...")

                        threshold = anomaly_scores.quantile(0.01)
                        anomaly_mask = anomaly_scores <= threshold
                        print(f"🔧 Adjusted threshold (1st percentile): {threshold:.4f}")
                else:

                    threshold = anomaly_scores.quantile(0.95)
                    anomaly_mask = anomaly_scores > threshold
                    print(f"🔍 DEBUG: Other algorithm - Higher scores are anomalies")
                    print(f"🔍 DEBUG: Threshold (95th percentile): {threshold:.4f}")
                
                print(f"🔍 DEBUG: Threshold: {threshold:.4f}")
                print(f"🔍 DEBUG: Anomalous unique logs: {anomaly_mask.sum()}")
                print(f"🔍 DEBUG: Total unique logs: {len(anomaly_mask)}")
                print(f"🔍 DEBUG: Anomaly percentage: {(anomaly_mask.sum() / len(anomaly_mask) * 100):.2f}%")
                
                if self.config.anomaly_detection_config.algo_name == "one_class_svm":
                    print(f"🔍 DEBUG: Number of scores <= threshold: {(anomaly_scores <= threshold).sum()}")
                    print(f"🔍 DEBUG: Number of scores < threshold: {(anomaly_scores < threshold).sum()}")
                    print(f"🔍 DEBUG: Number of scores == threshold: {(anomaly_scores == threshold).sum()}")
                    
                    if anomaly_mask.sum() == 0:
                        print("⚠️  WARNING: No anomalies detected with 5% threshold!")
                        print("🔧 Trying more aggressive threshold (10% percentile)...")
                        threshold = anomaly_scores.quantile(0.10)
                        anomaly_mask = anomaly_scores <= threshold
                        print(f"🔧 New threshold (10th percentile): {threshold:.4f}")
                        print(f"🔧 Anomalous unique logs with new threshold: {anomaly_mask.sum()}")
                    
                    elif anomaly_mask.sum() > len(anomaly_mask) * 0.5:
                        print("⚠️  WARNING: Too many anomalies detected (>50%)!")
                        print("🔧 Trying more conservative threshold (1% percentile)...")
                        threshold = anomaly_scores.quantile(0.01)
                        anomaly_mask = anomaly_scores <= threshold
                        print(f"🔧 New threshold (1st percentile): {threshold:.4f}")
                        print(f"🔧 Anomalous unique logs with new threshold: {anomaly_mask.sum()}")
                        
                        if anomaly_mask.sum() > len(anomaly_mask) * 0.2:
                            print("⚠️  WARNING: Still too many anomalies (>20%)!")
                            print("🔧 Using very conservative threshold (0.5% percentile)...")
                            threshold = anomaly_scores.quantile(0.005)
                            anomaly_mask = anomaly_scores <= threshold
                            print(f"🔧 Final threshold (0.5th percentile): {threshold:.4f}")
                            print(f"🔧 Anomalous unique logs with final threshold: {anomaly_mask.sum()}")
                        
                        if anomaly_mask.sum() > len(anomaly_mask) * 0.3:
                            print("⚠️  WARNING: Still detecting too many anomalies!")
                            print("🔧 Using fixed threshold based on score distribution...")

                            mean_score = anomaly_scores.mean()
                            std_score = anomaly_scores.std()
                            threshold = mean_score - 2 * std_score
                            anomaly_mask = anomaly_scores <= threshold
                            print(f"🔧 Fixed threshold (mean - 2*std): {threshold:.4f}")
                            print(f"🔧 Anomalous unique logs with fixed threshold: {anomaly_mask.sum()}")
                
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
                
                normalized_content_to_anomaly = {}
                inconsistencies = 0
                
                for idx, row in df.iterrows():
                    normalized_content = normalizer.normalize(row['logline'])
                    is_anomaly = row['is_anomaly']
                    
                    if normalized_content in normalized_content_to_anomaly:
                        if normalized_content_to_anomaly[normalized_content] != is_anomaly:
                            inconsistencies += 1
                            print(f"🚨 INCONSISTENCY: Normalized log '{normalized_content[:100]}...' has different classifications!")
                            print(f"   Original log: '{row['logline'][:100]}...'")
                    else:
                        normalized_content_to_anomaly[normalized_content] = is_anomaly
                
                print(f"🔍 DEBUG: Total logs: {len(df)}")
                print(f"🔍 DEBUG: Unique log contents: {len(normalized_content_to_anomaly)}")
                print(f"🔍 DEBUG: Anomalies detected: {df['is_anomaly'].sum()}")
                print(f"🔍 DEBUG: Inconsistencies found: {inconsistencies}")
                
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
        
        if log_record.attributes is not None and not log_record.attributes.empty:
            self._attributes = log_record.attributes.astype(str)
        else:

            self._attributes = pd.DataFrame()

        preprocessor = Preprocessor(self.config.preprocessor_config)
        preprocessed_loglines, _ = preprocessor.clean_log(logline)

        new_log_record = LogRecordObject(
            body=pd.DataFrame(preprocessed_loglines, columns=[constants.LOGLINE_NAME]),
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
