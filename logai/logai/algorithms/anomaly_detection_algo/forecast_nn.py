
from logai.algorithms.algo_interfaces import NNAnomalyDetectionAlgo
from logai.algorithms.nn_model.forecast_nn.base_nn import ForecastBasedNNParams
from logai.algorithms.vectorization_algo.forecast_nn import ForecastNNVectorizedDataset
from logai.algorithms.nn_model.forecast_nn.lstm import LSTM, LSTMParams
from logai.algorithms.nn_model.forecast_nn.cnn import CNN, CNNParams
from logai.algorithms.nn_model.forecast_nn.transformer import (
    Transformer,
    TransformerParams,
)
from logai.algorithms.factory import factory
from torch.utils.data import DataLoader

class ForcastBasedNeuralAD(NNAnomalyDetectionAlgo):
    
    def __init__(self, config: ForecastBasedNNParams):
        
        self.model = None
        self.config = config

    def fit(
        self,
        train_data: ForecastNNVectorizedDataset,
        dev_data: ForecastNNVectorizedDataset,
    ):
        
        dataloader_train = DataLoader(
            train_data.dataset,
            batch_size=self.config.batch_size,
            shuffle=False,
            pin_memory=True,
        )
        dataloader_dev = DataLoader(
            dev_data.dataset,
            batch_size=self.config.batch_size,
            shuffle=False,
            pin_memory=True,
        )
        self.model.fit(train_loader=dataloader_train, dev_loader=dataloader_dev)

    def predict(self, test_data: ForecastNNVectorizedDataset):
        
        dataloader_test = DataLoader(
            test_data.dataset,
            batch_size=self.config.batch_size,
            shuffle=False,
            pin_memory=True,
        )
        result = self.model.predict(test_loader=dataloader_test)
        return result

@factory.register("detection", "lstm", LSTMParams)
class ForecastBasedLSTM(ForcastBasedNeuralAD):
    
    def __init__(self, config: LSTMParams):
        super().__init__(config)
        self.config = config
        self.model = LSTM(config=self.config)

@factory.register("detection", "cnn", CNNParams)
class ForecastBasedCNN(ForcastBasedNeuralAD):
    
    def __init__(self, config: CNNParams):
        super().__init__(config)
        self.config = config
        self.model = CNN(config=self.config)

@factory.register("detection", "transformer", TransformerParams)
class ForecastBasedTransformer(ForcastBasedNeuralAD):
    
    def __init__(self, config: TransformerParams):
        super().__init__(config)
        self.config = config
        self.model = Transformer(config=self.config)
