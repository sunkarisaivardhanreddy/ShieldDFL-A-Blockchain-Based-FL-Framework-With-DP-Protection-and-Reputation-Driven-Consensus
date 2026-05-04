from django.db import models
from accounts.models import Device


class AttackLog(models.Model):
    """Logs of detected or simulated attacks"""
    ATTACK_TYPES = (
        ('SAR', 'Statistical Attack Replacement'),
        ('BASR', 'Backdoor Attack with Sample Replacement'),
    )
    
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='attack_logs')
    fl_round_id = models.CharField(max_length=100)
    fl_round_number = models.IntegerField(default=0)
    attack_type = models.CharField(max_length=10, choices=ATTACK_TYPES)
    is_malicious = models.BooleanField(default=False)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'attack_logs'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.attack_type} - {self.device.device_name} - Round {self.fl_round_number}"


class AnomalyDetectionResult(models.Model):
    """Stores anomaly detection scores"""
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='anomaly_results')
    fl_round_number = models.IntegerField(default=0)
    gradient_norm = models.FloatField(default=0.0)
    z_score = models.FloatField(default=0.0)
    is_anomalous = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'anomaly_detection_results'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Anomaly - {self.device.device_name} - Round {self.fl_round_number}"
