"""Management command to check device-user-update relationships."""

from django.core.management.base import BaseCommand
from accounts.models import Device
from federated_learning.models import ModelUpdate


class Command(BaseCommand):
    help = 'Check which devices have model updates and who owns them'

    def handle(self, *args, **options):
        updates = ModelUpdate.objects.select_related('device', 'device__user').all()[:15]
        
        self.stdout.write("=" * 60)
        self.stdout.write(f"Total ModelUpdate records: {ModelUpdate.objects.count()}")
        self.stdout.write("=" * 60)
        self.stdout.write("\nDevice -> User mapping for updates:")
        self.stdout.write("-" * 60)

        for u in updates:
            user_name = u.device.user.username if u.device.user else "No user"
            round_num = u.fl_round.round_number if u.fl_round else "?"
            self.stdout.write(f"{u.device.device_name:20} -> {user_name:15} (Round {round_num})")

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("Devices with no updates:")
        self.stdout.write("-" * 60)

        all_devices = Device.objects.all()
        for device in all_devices:
            update_count = ModelUpdate.objects.filter(device=device).count()
            user_name = device.user.username if device.user else "No user"
            if update_count == 0:
                self.stdout.write(f"{device.device_name:20} -> {user_name:15} (0 updates)")
        
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS('Check complete'))
