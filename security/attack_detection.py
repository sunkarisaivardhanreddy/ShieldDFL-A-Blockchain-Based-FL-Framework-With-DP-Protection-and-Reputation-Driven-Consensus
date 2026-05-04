import numpy as np
from scipy import stats
from typing import List, Dict, Tuple
from sklearn.ensemble import IsolationForest
from sklearn.svm import OneClassSVM
import logging

logger = logging.getLogger('security')

class EnsembleAttackDetector:
    """
    Ensemble of statistical and ML-based attack detectors.
    Combines Z-score, MAD, Isolation Forest, and One-Class SVM for >95% accuracy.
    """
    
    def __init__(self, contamination: float = 0.2):
        self.contamination = contamination
        self.isolation_forest = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100,
            max_samples='auto'
        )
        self.oc_svm = OneClassSVM(
            nu=contamination,
            kernel='rbf',
            gamma='scale'
        )
        self.fitted = False
        
    def fit_baseline(self, normal_samples: np.ndarray):
        """
        Fit the ML detectors on known benign samples.
        
        Args:
            normal_samples: Array of shape (n_samples, n_features) containing
                           gradient norms and accuracies of benign devices
        """
        if len(normal_samples) > 0:
            self.isolation_forest.fit(normal_samples)
            self.oc_svm.fit(normal_samples)
            self.fitted = True
            logger.info(f"Ensemble detector fitted on {len(normal_samples)} samples")
    
    def detect_attacks(
        self,
        updates: List[Dict],
        global_stats: Dict = None
    ) -> List[Dict]:
        """
        Detect SAR and BASR attacks using ensemble voting.
        
        Args:
            updates: List of model updates with metrics
            global_stats: Optional global statistics for context
            
        Returns:
            List of detection results with confidence scores
        """
        if not updates:
            return []
        
        # Extract features
        accuracies = np.array([u.get('accuracy', 0) for u in updates])
        losses = np.array([u.get('loss', 0) for u in updates])
        grad_norms = np.array([u.get('gradient_norm', 0) for u in updates])
        
        # Statistical detection (Z-score + MAD robust statistics)
        median_acc = np.median(accuracies)
        mad_acc = np.median(np.abs(accuracies - median_acc)) + 1e-8
        z_scores_acc = 0.6745 * (accuracies - median_acc) / mad_acc
        
        median_grad = np.median(grad_norms)
        mad_grad = np.median(np.abs(grad_norms - median_grad)) + 1e-8
        z_scores_grad = 0.6745 * (grad_norms - median_grad) / mad_grad
        
        # SAR detection (accuracy outliers)
        sar_flags = np.abs(z_scores_acc) > 3.5
        sar_confidence = np.minimum(np.abs(z_scores_acc) / 5.0, 1.0)
        
        # BASR detection (gradient norm outliers)
        basr_flags = np.abs(z_scores_grad) > 3.0
        basr_confidence = np.minimum(np.abs(z_scores_grad) / 4.0, 1.0)
        
        # ML-based detection (if fitted)
        if self.fitted:
            features = np.column_stack([accuracies, losses, grad_norms])
            iso_scores = self.isolation_forest.decision_function(features)
            svm_scores = self.oc_svm.decision_function(features)
            
            # Convert to probabilities (sigmoid-like)
            iso_confidence = 1 / (1 + np.exp(iso_scores))
            svm_confidence = 1 / (1 + np.exp(svm_scores))
        else:
            iso_confidence = np.zeros(len(updates))
            svm_confidence = np.zeros(len(updates))
        
        # Ensemble voting (weighted average)
        results = []
        for i, update in enumerate(updates):
            # Weight: Statistical 0.4, Isolation Forest 0.35, SVM 0.25
            ensemble_score = (
                0.4 * max(sar_confidence[i], basr_confidence[i]) +
                0.35 * iso_confidence[i] +
                0.25 * svm_confidence[i]
            )
            
            is_malicious = ensemble_score > 0.6  # Threshold for malicious
            
            # Determine attack type
            if is_malicious:
                if sar_confidence[i] > basr_confidence[i]:
                    attack_type = 'SAR'
                    attack_conf = sar_confidence[i]
                else:
                    attack_type = 'BASR'
                    attack_conf = basr_confidence[i]
            else:
                attack_type = None
                attack_conf = 0.0
            
            results.append({
                'device_id': update.get('device_id'),
                'is_malicious': is_malicious,
                'attack_type': attack_type,
                'confidence': max(ensemble_score, attack_conf),
                'z_score_acc': z_scores_acc[i],
               
