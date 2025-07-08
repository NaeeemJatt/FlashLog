
from .fasttext import FastText
from .semantic import Semantic
from .sequential import Sequential
from .tfidf import TfIdf
from .word2vec import Word2Vec
from logai.utils.misc import is_torch_available, \
    is_transformers_available

_MODULES = [
    "FastText",
    "Semantic",
    "Sequential",
    "TfIdf",
    "Word2Vec"
]

if is_torch_available() and is_transformers_available():
    from .forecast_nn import ForecastNN
    from .logbert import LogBERT

    _MODULES += [
        "ForecastNN",
        "LogBERT"
    ]

__all__ = _MODULES
