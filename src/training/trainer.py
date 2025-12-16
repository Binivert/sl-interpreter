"""Model training."""

import asyncio
import json
import logging
from pathlib import Path
from typing import Callable, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


class ModelTrainer:
    """Trains gesture recognition models."""
    
    def __init__(self, config: dict):
        self.config = config
        training_config = config.get("training", {})
        
        self.epochs = training_config.get("epochs", 50)
        self.batch_size = training_config.get("batch_size", 32)
        self.learning_rate = training_config.get("learning_rate", 0.001)
        self.validation_split = training_config.get("validation_split", 0.2)
        self.early_stopping_patience = training_config.get("early_stopping_patience", 10)
        
        self.models_dir = Path(config.get("models_dir", "models/gestures"))
        self.data_dir = Path(config.get("data_dir", "data/training"))
    
    async def train_incremental(
        self,
        sign_name: str,
        samples: List[np.ndarray],
        progress_callback: Optional[Callable] = None
    ) -> Dict:
        """Train incrementally to add a new sign.
        
        This adds a new sign to the existing model without full retraining.
        """
        
        from .augmentation import DataAugmenter
        from .exporter import ModelExporter
        
        logger.info(f"Starting incremental training for '{sign_name}'")
        
        # Augment data
        augmenter = DataAugmenter(self.config)
        augmented_samples = augmenter.augment(samples)
        
        if progress_callback:
            await progress_callback(0.1)
        
        # Prepare training data
        X, y = self._prepare_data(sign_name, augmented_samples)
        
        if progress_callback:
            await progress_callback(0.2)
        
        # Train model
        metrics = await self._train_model(X, y, progress_callback)
        
        # Export updated model
        exporter = ModelExporter(self.config)
        exporter.export_incremental(sign_name)
        
        if progress_callback:
            await progress_callback(1.0)
        
        return metrics
    
    def _prepare_data(self, sign_name: str, samples: List[np.ndarray]):
        """Prepare training data."""
        
        # Load existing training data
        existing_data = self._load_existing_data()
        
        # Add new samples
        X_new = np.array(samples)
        y_new = np.array([sign_name] * len(samples))
        
        if existing_data:
            X_existing, y_existing = existing_data
            X = np.vstack([X_existing, X_new])
            y = np.concatenate([y_existing, y_new])
        else:
            X = X_new
            y = y_new
        
        return X, y
    
    def _load_existing_data(self):
        """Load existing training data."""
        
        processed_dir = self.data_dir / "processed"
        
        if not processed_dir.exists():
            return None
        
        X_path = processed_dir / "X.npy"
        y_path = processed_dir / "y.npy"
        
        if X_path.exists() and y_path.exists():
            return np.load(X_path), np.load(y_path)
        
        return None
    
    async def _train_model(
        self,
        X: np.ndarray,
        y: np.ndarray,
        progress_callback: Optional[Callable] = None
    ) -> Dict:
        """Train the PyTorch model."""
        
        import torch
        import torch.nn as nn
        import torch.optim as optim
        from torch.utils.data import DataLoader, TensorDataset
        from sklearn.model_selection import train_test_split
        from sklearn.preprocessing import LabelEncoder
        
        # Encode labels
        label_encoder = LabelEncoder()
        y_encoded = label_encoder.fit_transform(y)
        
        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            X, y_encoded,
            test_size=self.validation_split,
            stratify=y_encoded
        )
        
        # Create tensors
        X_train_t = torch.FloatTensor(X_train)
        y_train_t = torch.LongTensor(y_train)
        X_val_t = torch.FloatTensor(X_val)
        y_val_t = torch.LongTensor(y_val)
        
        # Create data loaders
        train_dataset = TensorDataset(X_train_t, y_train_t)
        train_loader = DataLoader(train_dataset, batch_size=self.batch_size, shuffle=True)
        
        # Create model
        input_size = X.shape[1]
        num_classes = len(label_encoder.classes_)
        
        model = self._create_model(input_size, num_classes)
        
        # Loss and optimizer
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(model.parameters(), lr=self.learning_rate)
        
        # Training loop
        best_val_loss = float('inf')
        patience_counter = 0
        history = {'train_loss': [], 'val_loss': [], 'val_accuracy': []}
        
        for epoch in range(self.epochs):
            # Training
            model.train()
            train_loss = 0.0
            
            for batch_X, batch_y in train_loader:
                optimizer.zero_grad()
                outputs = model(batch_X)
                loss = criterion(outputs, batch_y)
                loss.backward()
                optimizer.step()
                train_loss += loss.item()
            
            train_loss /= len(train_loader)
            
            # Validation
            model.eval()
            with torch.no_grad():
                val_outputs = model(X_val_t)
                val_loss = criterion(val_outputs, y_val_t).item()
                
                _, predicted = torch.max(val_outputs, 1)
                val_accuracy = (predicted == y_val_t).float().mean().item()
            
            history['train_loss'].append(train_loss)
            history['val_loss'].append(val_loss)
            history['val_accuracy'].append(val_accuracy)
            
            # Early stopping
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
                # Save best model
                torch.save(model.state_dict(), self.models_dir / "custom" / "best_model.pt")
            else:
                patience_counter += 1
                if patience_counter >= self.early_stopping_patience:
                    logger.info(f"Early stopping at epoch {epoch}")
                    break
            
            # Progress callback
            if progress_callback:
                progress = 0.2 + 0.7 * (epoch / self.epochs)
                await progress_callback(progress)
            
            # Allow other tasks to run
            await asyncio.sleep(0)
        
        # Save labels
        labels_path = self.models_dir / "custom" / "labels.json"
        with open(labels_path, "w") as f:
            json.dump(list(label_encoder.classes_), f)
        
        return {
            "epochs_trained": epoch + 1,
            "final_train_loss": history['train_loss'][-1],
            "final_val_loss": history['val_loss'][-1],
            "final_val_accuracy": history['val_accuracy'][-1],
            "num_classes": num_classes
        }
    
    def _create_model(self, input_size: int, num_classes: int):
        """Create the neural network model."""
        
        import torch.nn as nn
        
        class GestureNet(nn.Module):
            def __init__(self, input_size, num_classes):
                super().__init__()
                self.network = nn.Sequential(
                    nn.Linear(input_size, 256),
                    nn.ReLU(),
                    nn.Dropout(0.3),
                    nn.Linear(256, 128),
                    nn.ReLU(),
                    nn.Dropout(0.3),
                    nn.Linear(128, 64),
                    nn.ReLU(),
                    nn.Linear(64, num_classes)
                )
            
            def forward(self, x):
                return self.network(x)
        
        return GestureNet(input_size, num_classes)
