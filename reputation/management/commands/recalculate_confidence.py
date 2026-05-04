from django.core.management.base import BaseCommand
from reputation.models import ReputationScore
from accounts.models import Device


class Command(BaseCommand):
    help = 'Recalculate confidence scores dynamically based on score deltas'

    def handle(self, *args, **options):
        """Recalculate confidence for all reputation scores based on delta from previous score"""
        updated_count = 0
        
        all_devices = Device.objects.all()
        
        for device in all_devices:
            # Get all scores for this device, ordered by round/timestamp
            scores = ReputationScore.objects.filter(device=device).order_by('round_number', 'timestamp')
            
            if not scores.exists():
                continue
                
            previous_score = 0.5  # Initial baseline
            
            for score_obj in scores:
                # Calculate delta from previous score
                delta = score_obj.score - previous_score
                # Confidence = 1.0 - abs(delta)  -- lower change = higher confidence
                new_confidence = max(0.0, min(1.0, 1.0 - abs(delta)))
                
                if abs(score_obj.confidence - new_confidence) > 0.001:  # Only update if different
                    score_obj.confidence = new_confidence
                    score_obj.save(update_fields=['confidence'])
                    updated_count += 1
                    self.stdout.write(
                        f"  {device.device_name} Round {score_obj.round_number}: "
                        f"delta={delta:.3f}, confidence={new_confidence:.3f}"
                    )
                
                previous_score = score_obj.score
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully updated {updated_count} confidence scores')
        )
