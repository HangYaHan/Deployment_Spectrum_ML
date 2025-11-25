import numpy as np
import torch
import os

try:
    mean = np.load('src/models/input_mean.npy')
    std = np.load('src/models/input_std.npy')
    print(f'Mean shape: {mean.shape}')
    print(f'Std shape: {std.shape}')
except Exception as e:
    print(f"Error loading numpy files: {e}")

try:
    state_dict = torch.load('src/models/model.pth', map_location='cpu')
    # print(f'State dict keys: {list(state_dict.keys())[:5]}')
    if 'fc.weight' in state_dict:
        print(f'FC weight shape: {state_dict["fc.weight"].shape}')
    else:
        print("fc.weight not found in state_dict")
except Exception as e:
    print(f"Error loading model: {e}")
