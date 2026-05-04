#!/usr/bin/env python
"""Test script to verify FL rounds display"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shielddfl.settings')
django.setup()

from federated_learning.models import FLRound
from accounts.models import Device

# Check total rounds
total_rounds = FLRound.objects.count()
print(f"✅ Total FL Rounds in database: {total_rounds}")

# List all rounds
if total_rounds > 0:
    print("\n📋 All FL Rounds:")
    for round_obj in FLRound.objects.all().order_by('-round_number'):
        print(f"  • Round {round_obj.round_number}: {round_obj.status} ({round_obj.current_participants}/{round_obj.max_participants} participants)")
else:
    print("⚠️  No FL rounds found! Creating test rounds...")
    
    # Create sample rounds
    for i in range(1, 6):
        fl_round = FLRound.objects.create(
            round_number=i,
            status='completed' if i < 5 else 'in_progress',
            min_participants=5,
            max_participants=50,
            current_participants=i * 3,
            global_model_accuracy=0.85 + (i * 0.01),
            global_model_loss=0.2 - (i * 0.02),
        )
        print(f"  ✓ Created Round {i}")
    
    print(f"\n✅ Created {FLRound.objects.count()} test rounds")

# Verify pagination
print("\n🔄 Testing Pagination (20 per page):")
from django.core.paginator import Paginator
all_rounds = FLRound.objects.all().order_by('-round_number')
paginator = Paginator(all_rounds, 20)
print(f"  • Total pages: {paginator.num_pages}")
print(f"  • Page 1: {paginator.page(1).object_list.count()} rounds")

# Verify device count
device_count = Device.objects.count()
print(f"\n🖥️  Total Devices: {device_count}")

print("\n✅ FL Rounds test complete!")
