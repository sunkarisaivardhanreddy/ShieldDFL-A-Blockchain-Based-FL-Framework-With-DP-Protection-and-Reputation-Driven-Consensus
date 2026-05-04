from django.db import models
from accounts.models import Device
import json


class Block(models.Model):
    """Persistent Blockchain Block Model"""
    index = models.IntegerField(unique=True)
    hash = models.CharField(max_length=64, unique=True)
    previous_hash = models.CharField(max_length=64)
    timestamp = models.DateTimeField()
    nonce = models.IntegerField(default=0)
    merkle_root = models.CharField(max_length=64)
    miner_device = models.ForeignKey(Device, on_delete=models.SET_NULL, null=True, related_name='mined_blocks')
    reputation_data = models.TextField(default='{}')  # JSON string
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'blocks'
        ordering = ['index']
    
    def __str__(self):
        return f"Block {self.index} - {self.hash[:8]}..."
    
    def get_reputation_data(self):
        return json.loads(self.reputation_data)
    
    def set_reputation_data(self, data):
        self.reputation_data = json.dumps(data)


class Transaction(models.Model):
    """Persistent Blockchain Transaction Model"""
    tx_hash = models.CharField(max_length=64, unique=True)
    sender = models.CharField(max_length=255)
    recipient = models.CharField(max_length=255)
    data = models.TextField()  # JSON string
    timestamp = models.DateTimeField()
    block = models.ForeignKey(Block, on_delete=models.CASCADE, related_name='transactions', null=True, blank=True)
    sender_device = models.ForeignKey(Device, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_transactions')
    
    class Meta:
        db_table = 'transactions'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"TX {self.tx_hash[:8]}... -> {self.recipient[:8]}..."
    
    def get_data(self):
        return json.loads(self.data)


class BlockchainLedger(models.Model):
    """Ledger for tracking FL rounds on blockchain"""
    entry_id = models.AutoField(primary_key=True)
    fl_round_id = models.CharField(max_length=100)
    block = models.ForeignKey(Block, on_delete=models.CASCADE, related_name='ledger_entries', null=True, blank=True)
    operation = models.CharField(max_length=50)  # START_ROUND, END_ROUND, MODEL_UPDATE
    device_count = models.IntegerField(default=0)
    global_model_hash = models.CharField(max_length=64, blank=True, null=True)
    metadata = models.TextField(default='{}')  # JSON
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'blockchain_ledger'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Ledger Entry {self.entry_id} - {self.operation}"
