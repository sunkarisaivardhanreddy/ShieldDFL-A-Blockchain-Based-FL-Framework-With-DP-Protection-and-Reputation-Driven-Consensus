import numpy as np
from math import sqrt, log


def gaussian_noise(scale, size):
    return np.random.normal(loc=0.0, scale=scale, size=size)


def laplace_noise(scale, size):
    return np.random.laplace(loc=0.0, scale=scale, size=size)


def apply_dp_to_gradients(gradients_dict, epsilon, delta, clip_norm=1.0, mechanism='gaussian'):
    """
    Apply DP mechanism to gradient dictionary.
    gradients_dict: param_name -> numpy array
    """
    dp_gradients = {}
    
    for name, values in gradients_dict.items():
        arr = np.array(values, dtype=np.float32)
        
        # Clip
        norm = np.linalg.norm(arr)
        if norm > clip_norm:
            arr = arr * (clip_norm / (norm + 1e-8))
        
        # Sensitivity for gradients (assume 1 for simplicity)
        sensitivity = 1.0
        
        if mechanism == 'gaussian':
            sigma = sqrt(2 * log(1.25 / delta)) * sensitivity / epsilon
            noise = gaussian_noise(sigma, arr.shape)
        else:
            b = sensitivity / epsilon
            noise = laplace_noise(b, arr.shape)
        
        dp_arr = arr + noise
        dp_gradients[name] = dp_arr.tolist()
    
    return dp_gradients
