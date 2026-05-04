from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import uuid

class User(AbstractUser):
    """Extended User Model"""
    USER_TYPE_CHOICES = (
        ('admin', 'Administrator'),
        ('device', 'Device Owner'),
        ('researcher', 'Researcher'),
    )
    
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='device')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    organization = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_verified = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.username} ({self.user_type})"


class Device(models.Model):
    """IIoT Device Model"""
    DEVICE_STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('blocked', 'Blocked'),
        ('suspended', 'Suspended'),
    )
    
    DEVICE_TYPE_CHOICES = (
        ('sensor', 'Sensor'),
        ('actuator', 'Actuator'),
        ('gateway', 'Gateway'),
        ('controller', 'Controller'),
        ('monitor', 'Monitor'),
    )
    
    device_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='devices')
    device_name = models.CharField(max_length=200)
    device_type = models.CharField(max_length=50, choices=DEVICE_TYPE_CHOICES, default='sensor')
    mac_address = models.CharField(max_length=17, unique=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    firmware_version = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(max_length=20, choices=DEVICE_STATUS_CHOICES, default='inactive')
    location = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    is_malicious = models.BooleanField(default=False)
    last_active = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'devices'
        verbose_name = 'Device'
        verbose_name_plural = 'Devices'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.device_name} ({self.device_id})"
    
    def activate(self):
        """Activate device"""
        self.status = 'active'
        self.save()
    
    def block(self):
        """Block malicious device"""
        self.status = 'blocked'
        self.is_malicious = True
        self.save()
    
    def get_reputation_score(self):
        """Get current reputation score"""
        from reputation.models import ReputationScore
        try:
            return ReputationScore.objects.filter(device=self).latest('timestamp').score
        except ReputationScore.DoesNotExist:
            return 0.5  # Default neutral score


class DeviceMetrics(models.Model):
    """Device Performance Metrics"""
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='metrics')
    cpu_usage = models.FloatField(default=0.0)
    memory_usage = models.FloatField(default=0.0)
    network_latency = models.FloatField(default=0.0)  # in ms
    battery_level = models.FloatField(default=100.0)  # percentage
    data_size = models.BigIntegerField(default=0)  # bytes
    uptime = models.IntegerField(default=0)  # seconds
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'device_metrics'
        verbose_name = 'Device Metric'
        verbose_name_plural = 'Device Metrics'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"Metrics for {self.device.device_name} at {self.timestamp}"
