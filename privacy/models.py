from django.db import models
from accounts.models import Device


class PrivacyBudget(models.Model):
    """
    Tracks dual privacy budgets:
    - query_epsilon: for statistical queries (SAR)
    - gradient_epsilon: for model updates
    """
    device = models.OneToOneField(Device, on_delete=models.CASCADE, related_name='privacy_budget')
    total_query_epsilon = models.FloatField(default=1.0)
    used_query_epsilon = models.FloatField(default=0.0)
    total_gradient_epsilon = models.FloatField(default=1.0)
    used_gradient_epsilon = models.FloatField(default=0.0)
    delta = models.FloatField(default=1e-5)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'privacy_budgets'
    
    def __str__(self):
        return f"Privacy Budget - {self.device.device_name}"
    
    @property
    def remaining_query_epsilon(self):
        return max(0.0, self.total_query_epsilon - self.used_query_epsilon)
    
    @property
    def remaining_gradient_epsilon(self):
        return max(0.0, self.total_gradient_epsilon - self.used_gradient_epsilon)
    
    def consume_query_budget(self, epsilon):
        self.used_query_epsilon += epsilon
        self.save()
    
    def consume_gradient_budget(self, epsilon):
        self.used_gradient_epsilon += epsilon
        self.save()
    
    def reset_budgets(self):
        self.used_query_epsilon = 0.0
        self.used_gradient_epsilon = 0.0
        self.save()
