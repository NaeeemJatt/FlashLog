
import os
import pathlib
import json
import pandas as pd
import yaml
import pickle as pkl

def file_exists(path: str):
    
    return os.path.exists(path)

def read_file(filepath: str):
    
    file_type = pathlib.Path(filepath).suffix
    if file_type == ".yaml":
        with open(filepath, "r") as stream:
            try:
                data = yaml.full_load(stream)
            except yaml.YAMLError as exc:
                raise exc
    elif file_type == ".json":
        with open(filepath, "r") as f:
            data = json.load(f)
    elif file_type == ".csv":
        with open(filepath, "r"):
            data = pd.read_csv(filepath)
    elif file_type == ".pkl" or file_type == ".pickle":
        data = pkl.load(open(filepath, "rb"))
    else:
        raise Exception("cannot read filetype", file_type)
    return data
