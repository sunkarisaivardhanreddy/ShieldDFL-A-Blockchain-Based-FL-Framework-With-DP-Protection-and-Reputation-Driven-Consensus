#!/usr/bin/env python
"""Check which devices have model updates and who owns them."""

from accounts.models import Device
from federated_learning.models import ModelUpdate

updates = ModelUpdate.objects.select_related('device', 'device__user').all()[:15]
print("=" * 60)
print(f"Total ModelUpdate records: {ModelUpdate.objects.count()}")
print("=" * 60)
print("\nDevice -> User mapping for updates:")
print("-" * 60)

for u in updates:
    user_name = u.device.user.username if u.device.user else "No user"
    round_num = u.fl_round.round_number if u.fl_round else "?"
    print(f"{u.device.device_name:20} -> {user_name:15} (Round {round_num})")

print("\n" + "=" * 60)
print("Devices with no updates:")
print("-" * 60)

all_devices = Device.objects.all()
for device in all_devices:
    update_count = ModelUpdate.objects.filter(device=device).count()
    user_name = device.user.username if device.user else "No user"
    if update_count == 0:
        print(f"{device.device_name:20} -> {user_name:15} (0 updates)")
