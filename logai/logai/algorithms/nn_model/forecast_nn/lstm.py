
import math
import torch
from torch import nn
from logai.algorithms.nn_model.forecast_nn.base_nn import (
    ForecastBasedNNParams,
    ForecastBasedNN,
)
from logai.algorithms.vectorization_algo.forecast_nn import ForecastNNVectorizedDataset
from attr import dataclass

@dataclass
class LSTMParams(ForecastBasedNNParams):
    
    num_directions: int = 2
    num_layers: int = 1
    max_token_len: int = None
    use_attention: bool = False

class Attention(nn.Module):
    
    def __init__(self, input_size, max_seq_len):
        
        super(Attention, self).__init__()
        self.atten_w = nn.Parameter(torch.randn(max_seq_len, input_size, 1))
        self.atten_bias = nn.Parameter(torch.randn(max_seq_len, 1, 1))
        self.glorot(self.atten_w)
        self.zeros(self.atten_bias)

    def forward(self, lstm_input):
        input_tensor = lstm_input.transpose(1, 0)
        input_tensor = (
            torch.bmm(input_tensor, self.atten_w) + self.atten_bias
        )
        input_tensor = input_tensor.transpose(1, 0)
        atten_weight = input_tensor.tanh()

        weighted_sum = torch.bmm(atten_weight.transpose(1, 2), lstm_input).squeeze()

        return weighted_sum

    def glorot(self, tensor):
        if tensor is not None:
            stdv = math.sqrt(6.0 / (tensor.size(-2) + tensor.size(-1)))
            tensor.data.uniform_(-stdv, stdv)

    def zeros(self, tensor):
        if tensor is not None:
            tensor.data.fill_(0)

class LSTM(ForecastBasedNN):
    
    def __init__(self, config: LSTMParams):
        
        super().__init__(config)
        self.config = config
        self.config.model_name = "lstm"
        num_labels = self.meta_data["num_labels"]
        self.feature_type = self.config.feature_type
        self.label_type = self.config.label_type
        self.hidden_size = self.config.hidden_size
        self.num_directions = self.config.num_directions
        self.max_token_len = self.config.max_token_len
        self.use_attention = self.config.use_attention
        self.embedding_dim = self.config.embedding_dim
        self.rnn = nn.LSTM(
            input_size=self.config.embedding_dim,
            hidden_size=self.hidden_size,
            batch_first=True,
            num_layers=self.config.num_layers,
            bidirectional=(self.config.num_directions == 2),
        )
        if self.use_attention:
            assert (
                self.max_token_len is not None
            ), "max token length must be set if using attention"
            self.attn = Attention(
                self.hidden_size * self.num_directions, self.max_token_len
            )
        self.criterion = nn.CrossEntropyLoss()
        self.prediction_layer = nn.Linear(
            self.hidden_size * self.num_directions, num_labels
        )

    def forward(self, input_dict):
        
        if self.label_type == "anomaly":
            y = input_dict[ForecastNNVectorizedDataset.window_anomalies].long().view(-1)
        elif self.label_type == "next_log":
            y = input_dict[ForecastNNVectorizedDataset.window_labels].long().view(-1)
        self.batch_size = y.size()[0]
        x = input_dict[ForecastNNVectorizedDataset.features]
        x = self.embedder(x)

        outputs, _ = self.rnn(x.float())
        if self.use_attention:
            representation = self.attn(outputs)
        else:

            representation = outputs[:, -1, :]

        logits = self.prediction_layer(representation)
        y_pred = logits.softmax(dim=-1)
        loss = self.criterion(logits, y)
        return_dict = {"loss": loss, "y_pred": y_pred}
        return return_dict
