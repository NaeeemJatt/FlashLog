
from transformers import AutoTokenizer
import os

def get_tokenizer(tokenizer_dirpath):
    
    return AutoTokenizer.from_pretrained(tokenizer_dirpath, use_fast=True)

def get_special_tokens():
    
    return [
        "[UNK]",
        "[PAD]",
        "[CLS]",
        "[SEP]",
        "[MASK]",
        ".",
        "*",
        ":",
        "$",
        "_",
        "-",
        "/",
    ]

def get_special_token_ids(tokenizer):
    
    return [tokenizer.convert_tokens_to_ids(x) for x in get_special_tokens()]

def get_tokenizer_vocab(tokenizer_dirpath):
    
    return open(os.path.join(tokenizer_dirpath, "vocab.txt")).readlines()

def get_mask_id(tokenizer):
    
    return tokenizer.convert_tokens_to_ids("[MASK]")
