from django.core.management.base import BaseCommand
from federated_learning.models import FLRound
from accounts.models import Device


class Command(BaseCommand):
    help = 'Test and verify FL Rounds display'

    def handle(self, *args, **options):
        self.stdout.write("🔍 Testing FL Rounds Display...\n")
        
        # Check total rounds
        total_rounds = FLRound.objects.count()
        self.stdout.write(f"✅ Total FL Rounds in database: {total_rounds}")

        # List all rounds
        if total_rounds > 0:
            self.stdout.write("\n📋 All FL Rounds:")
            for round_obj in FLRound.objects.all().order_by('-round_number'):
                self.stdout.write(
                    f"  • Round {round_obj.round_number}: {round_obj.status} "
                    f"({round_obj.current_participants}/{round_obj.max_participants} participants)"
                )
        else:
            self.stdout.write("\n⚠️  No FL rounds found! Creating test rounds...")
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
                self.stdout.write(f"  ✓ Created Round {i}")

            self.stdout.write(self.style.SUCCESS(f"\n✅ Created {FLRound.objects.count()} test rounds"))

        # List all rounds
        self.stdout.write("\n📋 Final FL Rounds List:")
        for round_obj in FLRound.objects.all().order_by('-round_number'):
            self.stdout.write(f"  • Round {round_obj.round_number}: {round_obj.status}")

        device_count = Device.objects.count()
        self.stdout.write(f"\n🖥️  Total Devices: {device_count}")
        
        self.stdout.write(self.style.SUCCESS("\n✅ FL Rounds test complete!"))
