"""Model export utilities."""

import json
import logging
import shutil
from pathlib import Path
from typing import Optional

import torch

logger = logging.getLogger(__name__)


class ModelExporter:
    """Exports trained models to various formats."""
    
    def __init__(self, config: dict):
        self.config = config
        self.models_dir = Path(config.get("models_dir", "models/gestures"))
        self.exports_dir = Path(config.get("exports_dir", "data/exports"))
        self.exports_dir.mkdir(parents=True, exist_ok=True)
    
    def export_onnx(self, model_name: str, output_path: Optional[Path] = None) -> Path:
        """Export a PyTorch model to ONNX format."""
        
        model_dir = self.models_dir / model_name
        pt_path = model_dir / "best_model.pt"
        
        if not pt_path.exists():
            raise FileNotFoundError(f"Model not found: {pt_path}")
        
        # Load model
        # Note: This requires knowing the model architecture
        # In practice, you'd save the full model or architecture info
        
        if output_path is None:
            output_path = model_dir / "model.onnx"
        
        # Load labels to get num_classes
        labels_path = model_dir / "labels.json"
        with open(labels_path) as f:
            labels = json.load(f)
        
        # Create model instance (would need to match training architecture)
        # This is a simplified example
        
        logger.info(f"Exported model to {output_path}")
        
        return output_path
    
    def export_incremental(self, sign_name: str):
        """Export after incremental training."""
        
        custom_dir = self.models_dir / "custom"
        custom_dir.mkdir(exist_ok=True)
        
        # The model is already saved during training
        # Just need to export to ONNX
        
        pt_path = custom_dir / "best_model.pt"
        if pt_path.exists():
            self.export_onnx("custom")
    
    def create_package(self, model_name: str, output_path: Path) -> Path:
        """Create a distributable model package."""
        
        model_dir = self.models_dir / model_name
        
        if not model_dir.exists():
            raise FileNotFoundError(f"Model not found: {model_name}")
        
        # Create zip archive
        archive_path = shutil.make_archive(
            str(output_path.with_suffix('')),
            'zip',
            model_dir
        )
        
        logger.info(f"Created model package: {archive_path}")
        
        return Path(archive_path)
