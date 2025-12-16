"""Model validation utilities."""

import logging
from typing import Dict, List, Tuple

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix
)

logger = logging.getLogger(__name__)


class ModelValidator:
    """Validates trained models."""
    
    def __init__(self, config: dict):
        self.config = config
    
    def validate(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        labels: List[str]
    ) -> Dict:
        """Compute validation metrics."""
        
        metrics = {
            "accuracy": accuracy_score(y_true, y_pred),
            "precision_macro": precision_score(y_true, y_pred, average='macro', zero_division=0),
            "recall_macro": recall_score(y_true, y_pred, average='macro', zero_division=0),
            "f1_macro": f1_score(y_true, y_pred, average='macro', zero_division=0)
        }
        
        # Per-class metrics
        precision_per_class = precision_score(y_true, y_pred, average=None, zero_division=0)
        recall_per_class = recall_score(y_true, y_pred, average=None, zero_division=0)
        
        metrics["per_class"] = {
            label: {
                "precision": float(precision_per_class[i]),
                "recall": float(recall_per_class[i])
            }
            for i, label in enumerate(labels)
        }
        
        # Confusion matrix
        cm = confusion_matrix(y_true, y_pred)
        metrics["confusion_matrix"] = cm.tolist()
        
        return metrics
    
    def cross_validate(
        self,
        X: np.ndarray,
        y: np.ndarray,
        n_folds: int = 5
    ) -> Dict:
        """Perform cross-validation."""
        
        from sklearn.model_selection import cross_val_score, StratifiedKFold
        
        # This would need a sklearn-compatible model wrapper
        # For now, return placeholder
        
        return {
            "cv_scores": [],
            "cv_mean": 0.0,
            "cv_std": 0.0
        }
