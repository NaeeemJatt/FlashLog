
from logai.applications.openset.anomaly_detection.openset_anomaly_detection_workflow import (
    OpenSetADWorkflow,
    get_openset_ad_config,
)
import os
import pytest

TEST_DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "test_data/HDFS_AD/HDFS_5k.log"
)
TEST_LABEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "test_data/HDFS_AD/anomaly_label.csv"
)
TEST_OUTPUT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "test_data/HDFS_AD/output"
)

class TestOpenSetLogAnomalyDetection:
    def _setup(self, config):
        config.data_loader_config.filepath = TEST_DATA_PATH
        config.label_filepath = TEST_LABEL_PATH
        config.output_dir = TEST_OUTPUT_PATH
        if not os.path.exists(config.output_dir):
            os.makedirs(config.output_dir)

    @pytest.mark.skip(reason="currently not testing this as this is time and memory consuming")
    def test_hdfs_logbert_ad(self):
        kwargs = {
            "config_filename": "hdfs",
            "anomaly_detection_type": "logbert_AD",
            "vectorizer_type": "logbert",
            "parse_logline": False,
            "training_type": "unsupervised",
        }
        config = get_openset_ad_config(**kwargs)
        self._setup(config)
        workflow = OpenSetADWorkflow(config)
        workflow.execute()

    def test_hdfs_lstm_sequential_unsupervised_parsed_ad(self):
        kwargs = {
            "config_filename": "hdfs",
            "anomaly_detection_type": "lstm_sequential_unsupervised_parsed_AD",
            "vectorizer_type": "forecast_nn_sequential",
            "parse_logline": True,
            "training_type": "unsupervised"
        }
        config = get_openset_ad_config(**kwargs)
        self._setup(config)
        workflow = OpenSetADWorkflow(config)
        workflow.execute()

    @pytest.mark.skip(reason="currently not testing this")
    def test_hdfs_lstm_sequential_supervised_parsed_ad(self):
        kwargs = {
            "config_filename": "hdfs",
            "anomaly_detection_type": "lstm_sequential_supervised_parsed_AD",
            "vectorizer_type": "forecast_nn_sequential",
            "parse_logline": True,
            "training_type": "supervised",
        }
        config = get_openset_ad_config(**kwargs)
        self._setup(config)
        workflow = OpenSetADWorkflow(config)
        workflow.execute()

    @pytest.mark.skip(reason="currently not testing this")
    def test_hdfs_lstm_sequential_unsupervised_nonparsed_ad(self):
        kwargs = {
            "config_filename": "hdfs",
            "anomaly_detection_type": "lstm_sequential_unsupervised_nonparsed_AD",
            "vectorizer_type": "forecast_nn_sequential",
            "parse_logline": False,
            "training_type": "unsupervised"
        }
        config = get_openset_ad_config(**kwargs)
        self._setup(config)
        workflow = OpenSetADWorkflow(config)
        workflow.execute()

    @pytest.mark.skip(reason="currently not testing this")
    def test_hdfs_lstm_sequential_supervised_nonparsed_ad(self):
        kwargs = {
            "config_filename": "hdfs",
            "anomaly_detection_type": "lstm_sequential_supervised_nonparsed_AD",
            "vectorizer_type": "forecast_nn_sequential",
            "parse_logline": False,
            "training_type": "supervised"
        }
        config = get_openset_ad_config(**kwargs)
        self._setup(config)
        workflow = OpenSetADWorkflow(config)
        workflow.execute()

    @pytest.mark.skip(reason="currently not testing this")
    def test_hdfs_lstm_semantics_supervised_nonparsed_ad(self):
        kwargs = {
            "config_filename": "hdfs",
            "anomaly_detection_type": "lstm_semantics_supervised_nonparsed_AD",
            "vectorizer_type": "forecast_nn_sequential",
            "parse_logline": True,
            "training_type": "supervised"
        }
        config = get_openset_ad_config(**kwargs)
        self._setup(config)
        workflow = OpenSetADWorkflow(config)
        workflow.execute()

    @pytest.mark.skip(reason="currently not testing this")
    def test_hdfs_lstm_semantics_unsupervised_nonparsed_ad(self):
        kwargs = {
            "config_filename": "hdfs",
            "anomaly_detection_type": "lstm_semantics_unsupervised_nonparsed_AD",
            "vectorizer_type": "forecast_nn_sequential",
            "parse_logline": True,
            "training_type": "unsupervised"
        }
        config = get_openset_ad_config(**kwargs)
        self._setup(config)
        workflow = OpenSetADWorkflow(config)
        workflow.execute()

    def test_hdfs_transformer_sequential_unsupervised_parsed_ad(self):
        kwargs = {
            "config_filename": "hdfs",
            "anomaly_detection_type": "transformer_sequential_unsupervised_parsed_AD",
            "vectorizer_type": "forecast_nn_sequential",
            "parse_logline": True,
            "training_type": "unsupervised"
        }
        config = get_openset_ad_config(**kwargs)
        self._setup(config)
        workflow = OpenSetADWorkflow(config)
        workflow.execute()

    @pytest.mark.skip(reason="currently not testing this")
    def test_hdfs_transformer_sequential_supervised_parsed_ad(self):
        kwargs = {
            "config_filename": "hdfs",
            "anomaly_detection_type": "transformer_sequential_supervised_parsed_AD",
            "vectorizer_type": "forecast_nn_sequential",
            "parse_logline": True,
            "training_type": "supervised"
        }
        config = get_openset_ad_config(**kwargs)
        self._setup(config)
        workflow = OpenSetADWorkflow(config)
        workflow.execute()

    @pytest.mark.skip(reason="currently not testing this")
    def test_hdfs_transformer_sequential_unsupervised_nonparsed_ad(self):
        kwargs = {
            "config_filename": "hdfs",
            "anomaly_detection_type": "transformer_sequential_unsupervised_nonparsed_AD",
            "vectorizer_type": "forecast_nn_sequential",
            "parse_logline": False,
            "training_type": "unsupervised"
        }
        config = get_openset_ad_config(**kwargs)
        self._setup(config)
        workflow = OpenSetADWorkflow(config)
        workflow.execute()

    @pytest.mark.skip(reason="currently not testing this")
    def test_hdfs_transformer_sequential_supervised_nonparsed_ad(self):
        kwargs = {
            "config_filename": "hdfs",
            "anomaly_detection_type": "transformer_sequential_supervised_nonparsed_AD",
            "vectorizer_type": "forecast_nn_sequential",
            "parse_logline": False,
            "training_type": "supervised"
        }
        config = get_openset_ad_config(**kwargs)
        self._setup(config)
        workflow = OpenSetADWorkflow(config)
        workflow.execute()

    @pytest.mark.skip(reason="currently not testing this")
    def test_hdfs_transformer_semantics_supervised_nonparsed_ad(self):
        kwargs = {
            "config_filename": "hdfs",
            "anomaly_detection_type": "transformer_semantics_supervised_nonparsed_AD",
            "vectorizer_type": "forecast_nn_sequential",
            "parse_logline": True,
            "training_type": "supervised"
        }
        config = get_openset_ad_config(**kwargs)
        self._setup(config)
        workflow = OpenSetADWorkflow(config)
        workflow.execute()

    @pytest.mark.skip(reason="currently not testing this")
    def test_hdfs_transformer_semantics_unsupervised_nonparsed_ad(self):
        kwargs = {
            "config_filename": "hdfs",
            "anomaly_detection_type": "transformer_semantics_unsupervised_nonparsed_AD",
            "vectorizer_type": "forecast_nn_sequential",
            "parse_logline": True,
            "training_type": "unsupervised"
        }
        config = get_openset_ad_config(**kwargs)
        self._setup(config)
        workflow = OpenSetADWorkflow(config)
        workflow.execute()

    def test_hdfs_cnn_sequential_unsupervised_parsed_ad(self):
        kwargs = {
            "config_filename": "hdfs",
            "anomaly_detection_type": "cnn_sequential_unsupervised_parsed_AD",
            "vectorizer_type": "forecast_nn_sequential",
            "parse_logline": True,
            "training_type": "unsupervised"
        }
        config = get_openset_ad_config(**kwargs)
        self._setup(config)
        workflow = OpenSetADWorkflow(config)
        workflow.execute()

    @pytest.mark.skip(reason="currently not testing this")
    def test_hdfs_cnn_sequential_supervised_parsed_ad(self):
        kwargs = {
            "config_filename": "hdfs",
            "anomaly_detection_type": "cnn_sequential_supervised_parsed_AD",
            "vectorizer_type": "forecast_nn_sequential",
            "parse_logline": True,
            "training_type": "supervised"
        }
        config = get_openset_ad_config(**kwargs)
        self._setup(config)
        workflow = OpenSetADWorkflow(config)
        workflow.execute()

    @pytest.mark.skip(reason="currently not testing this")
    def test_hdfs_cnn_sequential_unsupervised_nonparsed_ad(self):
        kwargs = {
            "config_filename": "hdfs",
            "anomaly_detection_type": "cnn_sequential_unsupervised_nonparsed_AD",
            "vectorizer_type": "forecast_nn_sequential",
            "parse_logline": False,
            "training_type": "unsupervised"
        }
        config = get_openset_ad_config(**kwargs)
        self._setup(config)
        workflow = OpenSetADWorkflow(config)
        workflow.execute()

    @pytest.mark.skip(reason="currently not testing this")
    def test_hdfs_cnn_sequential_supervised_nonparsed_ad(self):
        kwargs = {
            "config_filename": "hdfs",
            "anomaly_detection_type": "cnn_sequential_supervised_nonparsed_AD",
            "vectorizer_type": "forecast_nn_sequential",
            "parse_logline": False,
            "training_type": "supervised"
        }
        config = get_openset_ad_config(**kwargs)
        self._setup(config)
        workflow = OpenSetADWorkflow(config)
        workflow.execute()

    @pytest.mark.skip(reason="currently not testing this")
    def test_hdfs_cnn_semantics_supervised_nonparsed_ad(self):
        kwargs = {
            "config_filename": "hdfs",
            "anomaly_detection_type": "cnn_semantics_supervised_nonparsed_AD",
            "vectorizer_type": "forecast_nn_sequential",
            "parse_logline": True,
            "training_type": "supervised"
        }
        config = get_openset_ad_config(**kwargs)
        self._setup(config)
        workflow = OpenSetADWorkflow(config)
        workflow.execute()

    @pytest.mark.skip(reason="currently not testing this")
    def test_hdfs_cnn_semantics_unsupervised_nonparsed_ad(self):
        kwargs = {
            "config_filename": "hdfs",
            "anomaly_detection_type": "cnn_semantics_unsupervised_nonparsed_AD",
            "vectorizer_type": "forecast_nn_sequential",
            "parse_logline": True,
            "training_type": "unsupervised"
        }
        config = get_openset_ad_config(**kwargs)
        self._setup(config)
        workflow = OpenSetADWorkflow(config)
        workflow.execute()
