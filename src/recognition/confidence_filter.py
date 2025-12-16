"""Confidence filtering and smoothing for predictions."""

import logging
from collections import deque
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class ConfidenceFilter:
    """Filters predictions based on confidence and applies smoothing."""
    
    def __init__(self, threshold: float = 0.7, smoothing: float = 0.3):
        self.threshold = threshold
        self.smoothing = smoothing
        self.history: deque = deque(maxlen=5)
        self.last_prediction: Optional[str] = None
        self.last_confidence: float = 0.0
    
    def filter(self, prediction: str, confidence: float) -> Optional[str]:
        """Filter a prediction based on confidence.
        
        Returns:
            The prediction if it passes the filter, None otherwise.
        """
        
        # Apply exponential smoothing to confidence
        smoothed_confidence = self._smooth_confidence(prediction, confidence)
        
        # Add to history
        self.history.append((prediction, smoothed_confidence))
        
        # Check threshold
        if smoothed_confidence < self.threshold:
            return None
        
        # Check for stability (same prediction in recent history)
        if not self._is_stable(prediction):
            return None
        
        self.last_prediction = prediction
        self.last_confidence = smoothed_confidence
        
        return prediction
    
    def _smooth_confidence(self, prediction: str, confidence: float) -> float:
        """Apply exponential smoothing to confidence."""
        
        if self.last_prediction == prediction:
            return self.smoothing * confidence + (1 - self.smoothing) * self.last_confidence
        
        return confidence
    
    def _is_stable(self, prediction: str) -> bool:
        """Check if prediction is stable over recent history."""
        
        if len(self.history) < 3:
            return True
        
        # Count occurrences of this prediction in recent history
        recent = list(self.history)[-3:]
        count = sum(1 for p, _ in recent if p == prediction)
        
        return count >= 2
    
    def reset(self):
        """Reset the filter state."""
        
        self.history.clear()
        self.last_prediction = None
        self.last_confidence = 0.0
