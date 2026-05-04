# 📘 Device Management & Metrics System

## 🚀 Overview

This project is a Django-based system for managing devices, collecting and generating metrics, and simulating workflows such as federated learning.

---

## ⚙️ Setup on a New Laptop

### 1. Activate Virtual Environment

venv\\Scripts\\activate


### 2. Install Dependencies

pip install -r requirements.txt


### 3. Setup Database (MySQL)

Run this in your MySQL command line:

CREATE DATABASE shielddfl_db;


### 4. Apply Migrations

python manage.py makemigrations
python manage.py migrate


### 5. Create Admin User

python manage.py createsuperuser


---

## 🔄 Recommended Workflow

### Step 1: Activate Environment

venv\\Scripts\\activate


### Step 2: Create Test Devices

python scripts\\create_test_devices.py


### Step 3: Sync Devices & Update Reputation

python manage.py sync_devices --update-reputation


### Step 4: Collect Metrics

python manage.py collect_device_metrics


### Step 5: Limit Stored Metrics (Optional)

python manage.py collect_device_metrics --keep 50


### Step 6: Generate Test Metrics

python manage.py generate_metrics --count 20


### Step 7: Generate Dataset

cd datasets
python generate_datasets.py
cd ..


### Step 8: Run Server

python manage.py runserver


---

## 🧪 Testing & Utility Scripts

### Check Updates

python scripts\\check_updates.py


### Test Federated Learning Rounds

python scripts\\test_fl_rounds.py


### Test Metrics

python scripts\\test_metrics.py


### Test New Device Metrics

python scripts\\test_new_device_metrics.py


### Test Styling

python scripts\\test_styling.py


---
## ⚡ Notes

* Always activate the virtual environment before running commands
* Ensure MySQL server is running before migrations
* Run scripts after server setup for testing and validation
* Ignore any unknown commands like c unless defined locally

---

## 📌 Future Improvements

* Automate workflow using shell/batch scripts
* Add logging and monitoring
* Improve UI and analytics dashboards

---

## 👨‍💻 Author

Maintained for development and testing purposes




##### Device Cleanup (Using Custom Command)

python manage.py shell

from accounts.models import Device
Device.objects.all().delete()

Device.objects.count()

exit()
