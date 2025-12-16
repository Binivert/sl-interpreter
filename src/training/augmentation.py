"""Data augmentation for training."""

import logging
from typing import List

import numpy as np

logger = logging.getLogger(__name__)


class DataAugmenter:
    """Augments landmark data for training."""
    
    def __init__(self, config: dict):
        aug_config = config.get("augmentation", {})
        
        self.rotation_range = aug_config.get("rotation_range", 15)
        self.scale_range = tuple(aug_config.get("scale_range", [0.9, 1.1]))
        self.translation_range = aug_config.get("translation_range", 0.1)
        self.noise_factor = aug_config.get("noise_factor", 0.02)
        self.flip_horizontal = aug_config.get("flip_horizontal", False)
    
    def augment(self, samples: List[np.ndarray], multiplier: int = 5) -> List[np.ndarray]:
        """Augment a list of samples.
        
        Args:
            samples: List of landmark arrays
            multiplier: How many augmented versions to create per sample
        
        Returns:
            List of augmented samples (including originals)
        """
        
        augmented = list(samples)  # Keep originals
        
        for sample in samples:
            for _ in range(multiplier):
                aug_sample = self._augment_single(sample)
                augmented.append(aug_sample)
        
        logger.info(f"Augmented {len(samples)} samples to {len(augmented)}")
        
        return augmented
    
    def _augment_single(self, sample: np.ndarray) -> np.ndarray:
        """Apply random augmentations to a single sample."""
        
        result = sample.copy()
        
        # Random rotation (in 2D, around z-axis)
        if self.rotation_range > 0:
            angle = np.random.uniform(-self.rotation_range, self.rotation_range)
            result = self._rotate(result, angle)
        
        # Random scale
        if self.scale_range != (1.0, 1.0):
            scale = np.random.uniform(*self.scale_range)
            result = self._scale(result, scale)
        
        # Random translation
        if self.translation_range > 0:
            tx = np.random.uniform(-self.translation_range, self.translation_range)
            ty = np.random.uniform(-self.translation_range, self.translation_range)
            result = self._translate(result, tx, ty)
        
        # Add noise
        if self.noise_factor > 0:
            noise = np.random.normal(0, self.noise_factor, result.shape)
            result = result + noise
        
        # Horizontal flip (rarely used for signs as they're directional)
        if self.flip_horizontal and np.random.random() > 0.5:
            result = self._flip_horizontal(result)
        
        return result.astype(np.float32)
    
    def _rotate(self, landmarks: np.ndarray, angle_degrees: float) -> np.ndarray:
        """Rotate landmarks around center."""
        
        angle_rad = np.radians(angle_degrees)
        cos_a = np.cos(angle_rad)
        sin_a = np.sin(angle_rad)
        
        # Reshape to (N, 3) for x, y, z
        reshaped = landmarks.reshape(-1, 3)
        
        # Center
        center_x = reshaped[:, 0].mean()
        center_y = reshaped[:, 1].mean()
        
        # Rotate x, y
        x = reshaped[:, 0] - center_x
        y = reshaped[:, 1] - center_y
        
        new_x = x * cos_a - y * sin_a + center_x
        new_y = x * sin_a + y * cos_a + center_y
        
        reshaped[:, 0] = new_x
        reshaped[:, 1] = new_y
        
        return reshaped.flatten()
    
    def _scale(self, landmarks: np.ndarray, scale: float) -> np.ndarray:
        """Scale landmarks from center."""
        
        reshaped = landmarks.reshape(-1, 3)
        
        center = reshaped.mean(axis=0)
        
        scaled = (reshaped - center) * scale + center
        
        return scaled.flatten()
    
    def _translate(self, landmarks: np.ndarray, tx: float, ty: float) -> np.ndarray:
        """Translate landmarks."""
        
        reshaped = landmarks.reshape(-1, 3)
        
        reshaped[:, 0] += tx
        reshaped[:, 1] += ty
        
        return reshaped.flatten()
    
    def _flip_horizontal(self, landmarks: np.ndarray) -> np.ndarray:
        """Flip landmarks horizontally."""
        
        reshaped = landmarks.reshape(-1, 3)
        
        reshaped[:, 0] = 1.0 - reshaped[:, 0]
        
        return reshaped.flatten()
