#!/usr/bin/env python
"""Test metrics API endpoint"""
import os
import sys
import django

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shielddfl.settings')
django.setup()

from accounts.models import Device, DeviceMetrics
import json

# Get first device
dev = Device.objects.first()
if dev:
    metrics = DeviceMetrics.objects.filter(device=dev)
    print(f'✅ Device: {dev.device_name} (ID: {dev.device_id})')
    print(f'✅ Total metrics: {metrics.count()}')
    
    # Show recent 5
    recent = metrics.order_by('-timestamp')[:5]
    print('\n📊 Recent 5 metrics:')
    for m in recent:
        print(f'  {m.timestamp.strftime("%Y-%m-%d %H:%M:%S")} - CPU: {m.cpu_usage:.1f}%, Memory: {m.memory_usage:.1f}%, Battery: {m.battery_level:.1f}%')
    
    # Test JSON serialization (what API will return)
    data = []
    for m in metrics.order_by('-timestamp')[:5]:
        data.append({
            'timestamp': m.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'cpu_usage': float(m.cpu_usage),
            'memory_usage': float(m.memory_usage),
            'network_latency': float(m.network_latency),
            'battery_level': float(m.battery_level),
        })
    
    print(f'\n🔗 JSON API response sample:')
    print(json.dumps({'metrics': data[:2]}, indent=2))
else:
    print('❌ No devices found')
