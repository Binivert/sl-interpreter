"""Temporal buffer for gesture sequence tracking."""

import logging
from collections import deque
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


class TemporalBuffer:
    """Rolling buffer for temporal gesture sequences."""
    
    def __init__(self, window_size: int = 15):
        self.window_size = window_size
        self.buffer: deque = deque(maxlen=window_size)
        self.feature_size: Optional[int] = None
    
    def add(self, landmarks: np.ndarray):
        """Add landmarks to the buffer."""
        
        if self.feature_size is None:
            self.feature_size = landmarks.shape[0]
        
        self.buffer.append(landmarks)
    
    def get_sequence(self) -> Optional[np.ndarray]:
        """Get the current sequence if buffer is full.
        
        Returns:
            Numpy array of shape (window_size, feature_size) or None.
        """
        
        if len(self.buffer) < self.window_size:
            return None
        
        return np.array(list(self.buffer))
    
    def get_partial_sequence(self) -> np.ndarray:
        """Get partial sequence, padding if needed."""
        
        if len(self.buffer) == 0:
            return None
        
        sequence = list(self.buffer)
        
        # Pad with first frame if needed
        while len(sequence) < self.window_size:
            sequence.insert(0, sequence[0])
        
        return np.array(sequence)
    
    def clear(self):
        """Clear the buffer."""
        
        self.buffer.clear()
    
    def resize(self, new_size: int):
        """Resize the buffer."""
        
        old_data = list(self.buffer)
        self.window_size = new_size
        self.buffer = deque(maxlen=new_size)
        
        # Keep most recent frames
        for item in old_data[-new_size:]:
            self.buffer.append(item)
        
        logger.info(f"Buffer resized to {new_size}")
    
    def is_ready(self) -> bool:
        """Check if buffer has enough frames."""
        
        return len(self.buffer) >= self.window_size
    
    def __len__(self) -> int:
        return len(self.buffer)
