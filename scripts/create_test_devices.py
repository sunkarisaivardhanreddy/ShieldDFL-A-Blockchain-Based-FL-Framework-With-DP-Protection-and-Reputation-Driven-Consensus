#!/usr/bin/env python
"""
Script to create test devices for ShieldDFL
Run from project root: python scripts/create_test_devices.py
"""
import os
import sys
import random

# Add project root to Python path (FIX for ModuleNotFoundError)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shielddfl.settings')
import django
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import Device
from privacy.models import PrivacyBudget
from reputation.models import ReputationScore

User = get_user_model()


def create_devices(count=10):
    """Create test devices with proper relationships"""
    
    # Get or create test user
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={
            'email': 'test@shielddfl.test',
            'user_type': 'device',
            'first_name': 'Test',
            'last_name': 'User'
        }
    )
    
    if created:
        user.set_password('testpass123')
        user.save()
        print(f"✅ Created test user: {user.username}")
    
    device_types = ['sensor', 'actuator', 'gateway', 'controller', 'monitor']
    locations = ['Factory Floor A', 'Factory Floor B', 'Factory Floor C', 'Warehouse']
    
    created_count = 0
    
    for i in range(count):
        device_name = f'Test_Device_{i+1:03d}'
        
        # Skip if already exists
        if Device.objects.filter(device_name=device_name).exists():
            print(f"⏭️  Skipping {device_name} (already exists)")
            continue
        
        # Generate MAC address
        mac = f"00:16:3e:{random.randint(0,127):02x}:{random.randint(0,255):02x}:{random.randint(0,255):02x}"
        
        # Create device
        device = Device.objects.create(
            user=user,
            device_name=device_name,
            device_type=random.choice(device_types),
            mac_address=mac,
            ip_address=f'192.168.1.{random.randint(10,200)}',
            status='active',
            location=random.choice(locations),
            firmware_version=f'v{random.randint(1,5)}.{random.randint(0,9)}',
            description=f'Simulated IIoT device for testing',
            is_malicious=False
        )
        
        # Create privacy budget
        PrivacyBudget.objects.create(
            device=device,
            total_query_epsilon=1.0,
            used_query_epsilon=0.0,
            total_gradient_epsilon=1.0,
            used_gradient_epsilon=0.0,
            delta=1e-5
        )
        
        # Create initial reputation
        ReputationScore.objects.create(
            device=device,
            score=0.5 + random.uniform(-0.1, 0.1),  # Random around 0.5
            confidence=0.5,
            round_number=0
        )
        
        created_count += 1
        print(f"✅ Created: {device_name} ({device.device_type}) - MAC: {mac}")
    
    # Summary
    total_active = Device.objects.filter(status='active').count()
    total_devices = Device.objects.count()
    
    print(f"\n{'='*50}")
    print(f"📊 SUMMARY")
    print(f"{'='*50}")
    print(f"🆕 New devices created: {created_count}")
    print(f"✅ Total active devices: {total_active}")
    print(f"📦 Total devices in DB: {total_devices}")
    print(f"{'='*50}")
    
    if total_active < 5:
        print(f"⚠️  WARNING: You need at least 5 active devices to simulate FL rounds!")
        print(f"   Run: python scripts/create_test_devices.py {5 - total_active}")
    else:
        print(f"✅ You can now simulate FL rounds!")


if __name__ == '__main__':
    # Get count from command line argument, default to 10
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    create_devices(count)
