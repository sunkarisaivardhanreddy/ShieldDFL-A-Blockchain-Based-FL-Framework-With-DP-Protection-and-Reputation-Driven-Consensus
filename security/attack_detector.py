import numpy as np
from .models import AttackLog, AnomalyDetectionResult
from accounts.models import Device
from federated_learning.models import ModelUpdate
from django.utils import timezone
from django.conf import settings
import logging

logger = logging.getLogger('shielddfl')


def detect_sar_attack(updates):
    """
    Simple SAR detection:
    - Compare local accuracy vs global median
    - Extremely low or high outliers flagged
    """
    accuracies = np.array([u.local_accuracy for u in updates], dtype=np.float32)
    if len(accuracies) == 0:
        return []
    
    median = np.median(accuracies)
    mad = np.median(np.abs(accuracies - median)) + 1e-6
    z_scores = (accuracies - median) / mad
    
    flagged_indices = np.where(np.abs(z_scores) > 3.5)[0]
    return flagged_indices.tolist(), z_scores


def detect_basr_attack(updates):
    """
    Simple BASR detection:
    - Extreme gradient norms
    - Suspiciously perfect accuracy with low loss
    """
    norms = np.array([u.gradient_norm for u in updates], dtype=np.float32)
    if len(norms) == 0:
        return []
    
    mean = np.mean(norms)
    std = np.std(norms) + 1e-6
    z_scores = (norms - mean) / std
    
    flagged_indices = np.where(z_scores > 3.0)[0]
    return flagged_indices.tolist(), z_scores


def run_attack_detection(fl_round):
    """Run SAR and BASR detection for a given FL round"""
    updates = list(fl_round.updates.all().select_related('device'))
    if not updates:
        return
    
    sar_indices, sar_z = detect_sar_attack(updates)
    basr_indices, basr_z = detect_basr_attack(updates)
    
    for i, u in enumerate(updates):
        sar_flag = i in sar_indices
        basr_flag = i in basr_indices
        
        if sar_flag:
            AttackLog.objects.create(
                device=u.device,
                fl_round_id=str(fl_round.round_id),
                fl_round_number=fl_round.round_number,
                attack_type='SAR',
                is_malicious=True,
                description=f"SAR anomaly with z-score {sar_z[i]:.2f}"
            )
        
        if basr_flag:
            AttackLog.objects.create(
                device=u.device,
                fl_round_id=str(fl_round.round_id),
                fl_round_number=fl_round.round_number,
                attack_type='BASR',
                is_malicious=True,
                description=f"BASR anomaly with z-score {basr_z[i]:.2f}"
            )
        
        AnomalyDetectionResult.objects.create(
            device=u.device,
            fl_round_number=fl_round.round_number,
            gradient_norm=u.gradient_norm,
            z_score=float(max(abs(sar_z[i]), abs(basr_z[i])) if len(sar_z) > i and len(basr_z) > i else 0.0),
            is_anomalous=bool(sar_flag or basr_flag)
        )
        
        if sar_flag or basr_flag:
            u.is_malicious = True
            u.save()
            logger.warning(f"Attack detected for device {u.device.device_name} in round {fl_round.round_number}")
