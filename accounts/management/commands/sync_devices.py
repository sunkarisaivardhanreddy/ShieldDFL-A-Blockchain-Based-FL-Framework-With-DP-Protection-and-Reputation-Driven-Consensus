from django.core.management.base import BaseCommand
from django.db import transaction
from accounts.models import Device
from reputation.models import ReputationScore
from reputation.reputation_engine import ReputationEngine
from privacy.models import PrivacyBudget
from security.models import AnomalyDetectionResult, AttackLog
from federated_learning.models import ModelUpdate


class Command(BaseCommand):
    help = 'Sync and update all device data across modules (reputation, privacy, security)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--update-reputation',
            action='store_true',
            help='Force update reputation scores for all devices',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting device sync...'))
        
        devices = Device.objects.all()
        rep_engine = ReputationEngine()
        
        created_budgets = 0
        created_reputations = 0
        created_anomalies = 0
        updated_reputations = 0
        updated_malicious = 0

        for device in devices:
            self.stdout.write(f'Processing device: {device.device_name}')
            
            with transaction.atomic():
                # 1. Create privacy budget if missing
                budget, created = PrivacyBudget.objects.get_or_create(device=device)
                if created:
                    created_budgets += 1
                    self.stdout.write(f'  ✓ Created privacy budget')

                # 2. Create base reputation if missing (check for any existing scores first)
                if not ReputationScore.objects.filter(device=device).exists():
                    ReputationScore.objects.create(
                        device=device,
                        round_number=0,
                        score=0.5,
                        confidence=0.5
                    )
                    created_reputations += 1
                    self.stdout.write(f'  ✓ Created reputation score')

                # 3. Update reputation based on FL participation
                updates = ModelUpdate.objects.filter(device=device)
                if updates.exists() or options['update_reputation']:
                    latest_round = updates.order_by('-fl_round__round_number').first()
                    round_num = latest_round.fl_round.round_number if latest_round else 0
                    
                    try:
                        new_score = rep_engine.predict_reputation(device)
                        
                        # Get the latest score for comparison
                        latest_rep = ReputationScore.objects.filter(device=device).order_by('-timestamp').first()
                        old_score = float(latest_rep.score) if latest_rep else 0.5
                        
                        # Create new reputation entry
                        ReputationScore.objects.create(
                            device=device,
                            score=new_score,
                            confidence=0.8,
                            round_number=round_num
                        )
                        
                        updated_reputations += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'  ✓ Updated reputation: {old_score:.3f} → {new_score:.3f}'
                            )
                        )
                    except Exception as e:
                        self.stdout.write(
                            self.style.WARNING(f'  ⚠ Could not update reputation: {e}')
                        )

                # 4. Check for malicious behavior
                attack_count = AttackLog.objects.filter(device=device, is_malicious=True).count()
                malicious_updates = ModelUpdate.objects.filter(device=device, is_malicious=True).count()
                
                should_be_malicious = (attack_count > 0 or malicious_updates > 0)
                if device.is_malicious != should_be_malicious:
                    device.is_malicious = should_be_malicious
                    if should_be_malicious:
                        device.status = 'blocked'
                    device.save(update_fields=['is_malicious', 'status'])
                    updated_malicious += 1
                    status = 'MALICIOUS' if should_be_malicious else 'CLEAN'
                    self.stdout.write(
                        self.style.WARNING(f'  ⚠ Updated malicious status: {status}')
                    )

                # 5. Create anomaly detection record if missing
                if not AnomalyDetectionResult.objects.filter(device=device, fl_round_number=0).exists():
                    AnomalyDetectionResult.objects.create(
                        device=device,
                        fl_round_number=0,
                        gradient_norm=0.0,
                        z_score=0.0,
                        is_anomalous=device.is_malicious
                    )
                    created_anomalies += 1
                    self.stdout.write(f'  ✓ Created anomaly record')

        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('Sync complete!'))
        self.stdout.write(f'Privacy budgets created: {created_budgets}')
        self.stdout.write(f'Reputation scores created: {created_reputations}')
        self.stdout.write(f'Reputation scores updated: {updated_reputations}')
        self.stdout.write(f'Anomaly records created: {created_anomalies}')
        self.stdout.write(f'Malicious status updated: {updated_malicious}')
        self.stdout.write('='*50)
