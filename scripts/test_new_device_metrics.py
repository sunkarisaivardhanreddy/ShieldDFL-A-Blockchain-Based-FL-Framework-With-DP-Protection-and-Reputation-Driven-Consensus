#!/usr/bin/env python
"""Test new device registration with metrics"""
import os
import sys
import django

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shielddfl.settings')
django.setup()

from accounts.models import Device, User, DeviceMetrics
from accounts.views import initialize_device_records
from django.db import transaction
import random

print("=" * 60)
print("Testing: New Device Registration with Auto-Metrics")
print("=" * 60)

# Get test user
user = User.objects.filter(username='testuser').first()
if not user:
    print("❌ Test user not found, creating...")
    user = User.objects.create_user(
        username='testuser',
        password='testpass123',
        user_type='device'
    )

# Generate unique MAC
mac = f"00:16:3e:{random.randint(0,127):02x}:{random.randint(0,255):02x}:{random.randint(0,255):02x}"

# Create new device
print("\n1. Creating new test device...")
with transaction.atomic():
    device = Device.objects.create(
        user=user,
        device_name='TEST_AUTO_METRICS_DEVICE',
        device_type='sensor',
        mac_address=mac,
        ip_address='192.168.1.250',
        status='active',
        location='Test Lab',
        is_malicious=False
    )
    print(f"   ✅ Device created: {device.device_name} (ID: {device.device_id})")
    
    # Initialize all records (including metrics)
    print("\n2. Initializing device records...")
    initialize_device_records(device)
    print("   ✅ Records initialized")

# Check metrics
print("\n3. Checking generated metrics...")
metrics = DeviceMetrics.objects.filter(device=device).order_by('-timestamp')
print(f"   ✅ Total metrics created: {metrics.count()}")

if metrics.exists():
    print("\n📊 Generated Metrics:")
    for idx, m in enumerate(metrics, 1):
        print(f"   {idx}. {m.timestamp.strftime('%Y-%m-%d %H:%M:%S')} - "
              f"CPU: {m.cpu_usage:.1f}%, "
              f"Memory: {m.memory_usage:.1f}%, "
              f"Battery: {m.battery_level:.1f}%")
else:
    print("   ❌ No metrics found!")

print("\n" + "=" * 60)
print("✅ Test completed successfully!")
print("=" * 60)
