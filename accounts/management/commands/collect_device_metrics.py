from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import Device, DeviceMetrics
import random


class Command(BaseCommand):
    help = 'Generate new metrics for all active devices (simulates continuous data collection)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--keep',
            type=int,
            default=100,
            help='Keep only the last N metrics per device (older ones are deleted)'
        )

    def handle(self, *args, **options):
        keep_count = options['keep']
        all_devices = Device.objects.all()
        total_created = 0

        for device in all_devices:
            # Generate one new metric for each device
            DeviceMetrics.objects.create(
                device=device,
                cpu_usage=random.uniform(15, 85),
                memory_usage=random.uniform(25, 80),
                network_latency=random.uniform(5, 120),
                battery_level=max(0, min(100, random.uniform(40, 100))),
                data_size=random.randint(500000, 15000000),
                uptime=random.randint(1800, 43200),
                timestamp=timezone.now()
            )
            total_created += 1

            # Clean up: keep only the last N metrics per device
            old_metrics = DeviceMetrics.objects.filter(device=device).order_by('-timestamp')[keep_count:]
            old_count = old_metrics.count()
            if old_count > 0:
                old_metrics.delete()
                self.stdout.write(f'  🗑️  Cleanup: Deleted {old_count} old metrics for {device.device_name}')

        self.stdout.write(
            self.style.SUCCESS(f'✅ Generated {total_created} new metrics for all devices')
        )
