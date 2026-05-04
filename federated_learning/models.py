from django.db import models
from django.utils import timezone
from accounts.models import Device, User
import uuid
import json

class FLRound(models.Model):
    """Federated Learning Round"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )
    
    round_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    round_number = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    min_participants = models.IntegerField(default=5)
    max_participants = models.IntegerField(default=50)
    current_participants = models.IntegerField(default=0)
    global_model_accuracy = models.FloatField(default=0.0)
    global_model_loss = models.FloatField(default=0.0)
    aggregation_method = models.CharField(max_length=50, default='FedAvg')
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'fl_rounds'
        ordering = ['-round_number']
    
    def __str__(self):
        return f"FL Round {self.round_number} - {self.status}"
    
    def start_round(self):
        """Start FL round"""
        self.status = 'in_progress'
        self.started_at = timezone.now()
        self.save()
    
    def complete_round(self, accuracy, loss):
        """Complete FL round"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.global_model_accuracy = accuracy
        self.global_model_loss = loss
        self.save()


class ModelUpdate(models.Model):
    """Local Model Update from Device"""
    update_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    fl_round = models.ForeignKey(FLRound, on_delete=models.CASCADE, related_name='updates')
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='model_updates')
    model_weights = models.TextField()  # JSON serialized weights
    local_accuracy = models.FloatField(default=0.0)
    local_loss = models.FloatField(default=0.0)
    training_samples = models.IntegerField(default=0)
    is_malicious = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    gradient_norm = models.FloatField(default=0.0)
    privacy_budget_used = models.FloatField(default=0.0)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'model_updates'
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"Update from {self.device.device_name} - Round {self.fl_round.round_number}"
    
    def get_weights(self):
        """Deserialize model weights"""
        return json.loads(self.model_weights)
    
    def set_weights(self, weights):
        """Serialize model weights"""
        self.model_weights = json.dumps(weights)


class GlobalModel(models.Model):
    """Global Federated Model"""
    model_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    fl_round = models.OneToOneField(FLRound, on_delete=models.CASCADE, related_name='global_model')
    model_architecture = models.CharField(max_length=100, default='SimpleCNN')
    model_weights = models.TextField()  # JSON serialized
    model_file_path = models.FileField(upload_to='models/global/', null=True, blank=True)
    accuracy = models.FloatField(default=0.0)
    loss = models.FloatField(default=0.0)
    num_parameters = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'global_models'
    
    def __str__(self):
        return f"Global Model - Round {self.fl_round.round_number}"


class TrainingMetrics(models.Model):
    """Training Metrics for each round"""
    fl_round = models.ForeignKey(FLRound, on_delete=models.CASCADE, related_name='metrics')
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='training_metrics')
    epoch = models.IntegerField()
    batch_accuracy = models.FloatField(default=0.0)
    batch_loss = models.FloatField(default=0.0)
    learning_rate = models.FloatField(default=0.01)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'training_metrics'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"Metrics - {self.device.device_name} - Epoch {self.epoch}"
