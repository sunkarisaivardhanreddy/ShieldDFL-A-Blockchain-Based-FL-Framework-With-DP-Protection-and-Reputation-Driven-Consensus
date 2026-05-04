import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from django.conf import settings
from .lstm_models.lstm_reputation import ReputationLSTM
from .models import ReputationScore, ReputationHistory
from accounts.models import Device
from security.models import AttackLog
from django.utils import timezone
import logging

logger = logging.getLogger('shielddfl')


class ReputationEngine:
    """Handles LSTM training and inference for reputation"""
    
    def __init__(self, model_path=None):
        self.model = ReputationLSTM()
        self.criterion = nn.MSELoss()
        self.optimizer = optim.Adam(self.model.parameters(), lr=0.001)
        self.model_path = model_path or (settings.MEDIA_ROOT / 'models' / 'reputation_lstm.pth')
        self._load_model()
    
    def _load_model(self):
        try:
            self.model.load_state_dict(torch.load(self.model_path))
            self.model.eval()
            logger.info("Loaded Reputation LSTM model")
        except Exception:
            logger.warning("Reputation LSTM model not found, using fresh model")
    
    def save_model(self):
        torch.save(self.model.state_dict(), self.model_path)
        logger.info("Reputation LSTM model saved")
    
    def build_feature_vector(self, device: Device, last_n: int = 10):
        """
        Build input sequence for LSTM:
        [local_accuracy, local_loss, gradient_norm, is_attack_flag]
        """
        from federated_learning.models import ModelUpdate
        from security.models import AttackLog
        
        updates = ModelUpdate.objects.filter(device=device).order_by('-uploaded_at')[:last_n]
        attacks = {a.fl_round_id for a in AttackLog.objects.filter(device=device, is_malicious=True)}
        
        seq = []
        for u in reversed(updates):
            is_attack = 1.0 if str(u.fl_round.round_id) in attacks or u.is_malicious else 0.0
            seq.append([
                float(u.local_accuracy) / 100.0,
                float(u.local_loss),
                float(u.gradient_norm),
                is_attack
            ])
        
        if not seq:
            seq = [[0.5, 0.5, 0.5, 0.0]] * last_n
        
        x = np.array(seq, dtype=np.float32)
        x = x.reshape(1, x.shape[0], x.shape[1])
        return torch.tensor(x)
    
    def predict_reputation(self, device: Device) -> float:
        """Run LSTM to predict next reputation score"""
        self.model.eval()
        x = self.build_feature_vector(device)
        with torch.no_grad():
            pred = self.model(x)
        score = float(pred.item())
        return max(0.0, min(1.0, score))
    
    def update_reputation(self, device: Device, round_number: int, reason: str = "") -> ReputationScore:
        """Update device reputation and save history"""
        try:
            last_score_obj = ReputationScore.objects.filter(device=device).latest('timestamp')
            old_score = float(last_score_obj.score)
        except ReputationScore.DoesNotExist:
            old_score = 0.5
        
        predicted_score = self.predict_reputation(device)
        
        # Penalize if recent attack logs
        recent_attacks = AttackLog.objects.filter(device=device, fl_round_number=round_number, is_malicious=True)
        if recent_attacks.exists():
            predicted_score *= 0.7
        
        new_score = max(0.0, min(1.0, predicted_score))
        delta = new_score - old_score
        
        rep_obj = ReputationScore.objects.create(
            device=device,
            score=new_score,
            confidence=1.0 - abs(delta),
            round_number=round_number
        )
        
        ReputationHistory.objects.create(
            device=device,
            event_type='update',
            delta_score=delta,
            old_score=old_score,
            new_score=new_score,
            reason=reason,
            round_number=round_number
        )
        
        logger.info(f"Reputation updated for {device.device_name}: {old_score:.3f} -> {new_score:.3f}")
        return rep_obj
