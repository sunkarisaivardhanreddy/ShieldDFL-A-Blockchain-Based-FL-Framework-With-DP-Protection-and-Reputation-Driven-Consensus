"""
Generate synthetic IIoT dataset for federated training.
"""
import numpy as np
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
OUT_FILE = BASE_DIR / 'iiot_data.csv'

def main():
    np.random.seed(42)
    num_samples = 10000
    num_devices = 50
    
    device_ids = np.random.randint(0, num_devices, size=num_samples)
    temperature = np.random.normal(60, 10, size=num_samples)
    pressure = np.random.normal(30, 5, size=num_samples)
    vibration = np.random.normal(5, 1, size=num_samples)
    load = np.random.uniform(0, 1, size=num_samples)
    
    failure_prob = (temperature - 50) / 30 + (pressure - 25) / 20 + vibration / 10 + load
    failure_prob = 1 / (1 + np.exp(-failure_prob))
    label = (failure_prob > 0.7).astype(int)
    
    df = pd.DataFrame({
        'device_id': device_ids,
        'temperature': temperature,
        'pressure': pressure,
        'vibration': vibration,
        'load': load,
        'failure': label,
    })
    
    df.to_csv(OUT_FILE, index=False)
    print(f"Dataset saved to {OUT_FILE}")

if __name__ == '__main__':
    main()
