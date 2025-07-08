
import gensim
import numpy as np
import pandas as pd
from attr import dataclass

from nltk.tokenize import word_tokenize
from logai.algorithms.algo_interfaces import VectorizationAlgo
from logai.config_interfaces import Config
from logai.algorithms.factory import factory

@dataclass
class Word2VecParams(Config):
    
    max_token_len: int = 100
    min_count: int = 1
    vector_size: int = 3
    window: int = 3

@factory.register("vectorization", "word2vec", Word2VecParams)
class Word2Vec(VectorizationAlgo):
    
    def __init__(self, params: Word2VecParams):
        self.params = params
        self.model = None

    def fit(self, loglines: pd.Series):
        
        max_token_len = self.params.max_token_len

        doc = []
        for sentence in loglines:
            token_list = sentence.split(" ")[:max_token_len]
            for tk in token_list:
                if tk != "*":
                    doc.append(word_tokenize(tk.lower()))

        self.model = gensim.models.Word2Vec(
            doc,
            min_count=self.params.min_count,
            vector_size=self.params.vector_size,
            window=self.params.window,
        )

    def transform(self, loglines: pd.Series) -> pd.Series:
        
        log_vectors = []
        max_len = 0
        for ll in loglines:
            token_list = ll.split(" ")

            log_vector = []

            token_list = token_list[: self.params.max_token_len]

            max_len = max(max_len, len(token_list))
            for tk in token_list:
                if tk == "*":
                    continue
                log_vector.append(self.model.wv[word_tokenize(tk.lower())][0])
            log_vectors.append(np.array(log_vector).flatten())
        log_vector_series = pd.Series(log_vectors, index=loglines.index)
        return log_vector_series

    def summary(self):
        
        return self.model.summary()
