from django.db import models
from accounts.models import Device
from django.utils import timezone


class ReputationScore(models.Model):
    """Current reputation score for a device"""
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='reputation_scores')
    score = models.FloatField(default=0.5)
    confidence = models.FloatField(default=0.5)
    round_number = models.IntegerField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'reputation_scores'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.device.device_name} - {self.score:.3f}"


class ReputationHistory(models.Model):
    """History of reputation-related events"""
    EVENT_TYPES = (
        ('update', 'Update'),
        ('penalty', 'Penalty'),
        ('reward', 'Reward'),
        ('attack_detected', 'Attack Detected'),
    )
    
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='reputation_history')
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    delta_score = models.FloatField(default=0.0)
    old_score = models.FloatField(default=0.5)
    new_score = models.FloatField(default=0.5)
    reason = models.TextField(blank=True, null=True)
    round_number = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'reputation_history'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.device.device_name} - {self.event_type} ({self.delta_score:+.3f})"
