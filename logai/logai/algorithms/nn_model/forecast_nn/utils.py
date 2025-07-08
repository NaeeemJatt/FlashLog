
import torch
import random
import os
import numpy as np

def tensor2flatten_arr(tensor):
    
    return tensor.data.cpu().numpy().reshape(-1)

def seed_everything(seed=1234):
    
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

def set_device(gpu: int = None):
    
    if not gpu:
        if torch.cuda.is_available():
            device = torch.device("cuda:" + str(torch.cuda.current_device()))
        else:
            device = torch.device("cpu")
    else:
        device = torch.device("cuda:" + str(gpu))
    return device
