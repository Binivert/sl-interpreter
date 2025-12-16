"""Sample capture for training."""

import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


class CaptureManager:
    """Manages sample capture for training new signs."""
    
    def __init__(self, config: dict):
        self.config = config
        self.data_dir = Path(config.get("data_dir", "data/training/raw"))
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.samples: Dict[str, List[np.ndarray]] = {}
        self.metadata: Dict[str, dict] = {}
    
    def add_sample(self, sign_name: str, landmarks: np.ndarray):
        """Add a landmark sample for a sign."""
        
        if sign_name not in self.samples:
            self.samples[sign_name] = []
            self.metadata[sign_name] = {
                "created": time.time(),
                "category": "custom"
            }
        
        self.samples[sign_name].append(landmarks)
        
        logger.debug(f"Added sample for '{sign_name}': {len(self.samples[sign_name])} total")
    
    def get_samples(self, sign_name: str) -> List[np.ndarray]:
        """Get all samples for a sign."""
        
        return self.samples.get(sign_name, [])
    
    def get_sample_count(self, sign_name: str) -> int:
        """Get the number of samples for a sign."""
        
        return len(self.samples.get(sign_name, []))
    
    def clear_samples(self, sign_name: str):
        """Clear samples for a sign."""
        
        if sign_name in self.samples:
            del self.samples[sign_name]
            del self.metadata[sign_name]
    
    def save_samples(self, sign_name: str):
        """Save samples to disk."""
        
        if sign_name not in self.samples:
            return
        
        sign_dir = self.data_dir / sign_name
        sign_dir.mkdir(exist_ok=True)
        
        # Save samples as numpy arrays
        for i, sample in enumerate(self.samples[sign_name]):
            sample_path = sign_dir / f"sample_{i:04d}.npy"
            np.save(sample_path, sample)
        
        # Save metadata
        metadata_path = sign_dir / "metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(self.metadata[sign_name], f, indent=2)
        
        logger.info(f"Saved {len(self.samples[sign_name])} samples for '{sign_name}'")
    
    def load_samples(self, sign_name: str) -> List[np.ndarray]:
        """Load samples from disk."""
        
        sign_dir = self.data_dir / sign_name
        
        if not sign_dir.exists():
            return []
        
        samples = []
        for sample_path in sorted(sign_dir.glob("sample_*.npy")):
            samples.append(np.load(sample_path))
        
        return samples
    
    def list_captured_signs(self) -> List[str]:
        """List all captured signs."""
        
        signs = list(self.samples.keys())
        
        # Also check disk
        for sign_dir in self.data_dir.iterdir():
            if sign_dir.is_dir() and sign_dir.name not in signs:
                signs.append(sign_dir.name)
        
        return signs
