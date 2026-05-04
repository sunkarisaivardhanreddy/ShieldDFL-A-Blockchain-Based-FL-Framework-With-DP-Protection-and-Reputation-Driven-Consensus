from django.core.management.base import BaseCommand
from federated_learning.models import FLRound, ModelUpdate
from accounts.models import Device
import random
import json


class Command(BaseCommand):
    help = 'Create model updates for a specific FL round'

    def add_arguments(self, parser):
        parser.add_argument('--round', type=int, default=26, help='Round number')

    def handle(self, *args, **options):
        round_num = options['round']
        
        try:
            fl_round = FLRound.objects.get(round_number=round_num)
        except FLRound.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Round {round_num} not found"))
            return

        devices = Device.objects.all()
        
        if not devices.exists():
            self.stdout.write(self.style.ERROR("No devices found"))
            return

        # Delete existing updates for this round
        existing_count = fl_round.updates.count()
        fl_round.updates.all().delete()
        self.stdout.write(f"Cleared {existing_count} existing updates")

        # Create model updates for each device
        self.stdout.write(f"\n📝 Creating updates for Round {round_num}...")
        created_count = 0
        
        for device in devices:
            update = ModelUpdate.objects.create(
                fl_round=fl_round,
                device=device,
                model_weights=json.dumps({"layer1": [random.random() for _ in range(5)]}),
                local_accuracy=round(random.uniform(0.7, 0.95), 2),
                local_loss=round(random.uniform(0.1, 0.4), 4),
                training_samples=random.randint(100, 500),
                is_malicious=random.choice([False, False, False, True]),  # 25% chance malicious
                gradient_norm=round(random.uniform(0.01, 0.1), 4),
                privacy_budget_used=round(random.uniform(0.1, 0.5), 3),
            )
            self.stdout.write(f"  ✓ {device.device_name}: {update.local_accuracy}% acc, Loss: {update.local_loss}")
            created_count += 1

        self.stdout.write(self.style.SUCCESS(f"\n✅ Created {created_count} model updates for Round {round_num}"))
        self.stdout.write(f"📊 Total updates in Round {round_num}: {fl_round.updates.count()}")
