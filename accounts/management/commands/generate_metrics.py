from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import Device, DeviceMetrics
import random
from datetime import timedelta


class Command(BaseCommand):
    help = 'Generate random metrics for all devices'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=10,
            help='Number of metric records to generate per device'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear all existing metrics before generating new ones'
        )

    def handle(self, *args, **options):
        count = options['count']
        clear = options['clear']

        if clear:
            deleted, _ = DeviceMetrics.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f'Deleted {deleted} existing metrics'))

        all_devices = Device.objects.all()
        total_created = 0

        for device in all_devices:
            now = timezone.now()
            
            for i in range(count):
                # Create metrics going back in time (most recent first)
                minutes_back = count - i
                timestamp = now - timedelta(minutes=minutes_back)
                
                # Generate realistic metrics with some variation
                cpu_usage = random.uniform(10, 90)
                memory_usage = random.uniform(20, 85)
                network_latency = random.uniform(5, 100)
                battery_level = max(0, min(100, random.uniform(30, 100)))
                
                # Add some correlation - high CPU might mean high memory
                if cpu_usage > 70:
                    memory_usage = min(100, memory_usage + random.uniform(5, 15))
                
                DeviceMetrics.objects.create(
                    device=device,
                    cpu_usage=cpu_usage,
                    memory_usage=memory_usage,
                    network_latency=network_latency,
                    battery_level=battery_level,
                    data_size=random.randint(1000000, 10000000),
                    uptime=random.randint(3600, 86400),
                    timestamp=timestamp
                )
                total_created += 1
            
            self.stdout.write(f'✅ Generated {count} metrics for {device.device_name}')

        self.stdout.write(
            self.style.SUCCESS(f'\nTotal metrics generated: {total_created}')
        )
