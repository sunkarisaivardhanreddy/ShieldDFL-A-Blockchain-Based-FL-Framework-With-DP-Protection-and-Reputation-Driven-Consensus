import numpy as np


def simulate_sar_attack(local_weights, severity=0.5):
    """
    SAR: replace statistics to bias the global model.
    Here we scale some parameters aggressively.
    """
    attacked = {}
    for name, values in local_weights.items():
        arr = np.array(values, dtype=np.float32)
        if 'weight' in name or 'bias' in name:
            factor = 1.0 + severity * np.sign(np.mean(arr) + 1e-6)
            arr *= factor
        attacked[name] = arr.tolist()
    return attacked


def simulate_basr_attack(local_weights, backdoor_pattern=0.1):
    """
    BASR: inject backdoor pattern into weights.
    For simplicity, add small constant offset.
    """
    attacked = {}
    for name, values in local_weights.items():
        arr = np.array(values, dtype=np.float32)
        if 'fc2.weight' in name:
            arr += backdoor_pattern
        attacked[name] = arr.tolist()
    return attacked
