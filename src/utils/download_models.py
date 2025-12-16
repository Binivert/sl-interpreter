"""Download default models."""

import logging
import urllib.request
import zipfile
from pathlib import Path

logger = logging.getLogger(__name__)

MODEL_URLS = {
    "asl_base": "https://example.com/models/asl_base.zip",  # Placeholder
    "en_amy": "https://example.com/voices/en_amy.zip",  # Placeholder
}


def download_default_models(models_dir: Path = Path("models")):
    """Download default models if not present."""
    
    models_dir.mkdir(parents=True, exist_ok=True)
    
    # Check for gesture models
    gestures_dir = models_dir / "gestures" / "asl_base"
    if not gestures_dir.exists():
        logger.info("Default gesture model not found")
        logger.info("Please download a gesture model or train your own")
        logger.info("See README.md for instructions")
        
        # Create placeholder structure
        gestures_dir.mkdir(parents=True, exist_ok=True)
        
        # Create placeholder files
        labels = ["hello", "thanks", "yes", "no", "help"]
        with open(gestures_dir / "labels.json", "w") as f:
            import json
            json.dump(labels, f)
        
        with open(gestures_dir / "config.yaml", "w") as f:
            f.write("name: ASL Base\nversion: 1.0.0\n")
    
    # Check for voice models
    voices_dir = models_dir / "voices" / "en_amy"
    if not voices_dir.exists():
        logger.info("Default voice model not found")
        logger.info("Download Piper voices from: https://github.com/rhasspy/piper/releases")
        
        voices_dir.mkdir(parents=True, exist_ok=True)
    
    # Check for language packs
    languages_dir = models_dir / "languages" / "en_US"
    if not languages_dir.exists():
        languages_dir.mkdir(parents=True, exist_ok=True)
        
        # Create default mappings
        mappings = {
            "language": "English (US)",
            "code": "en_US",
            "signs": {
                "hello": "Hello",
                "thanks": "Thank you",
                "yes": "Yes",
                "no": "No",
                "help": "Help"
            }
        }
        
        with open(languages_dir / "mappings.json", "w") as f:
            import json
            json.dump(mappings, f, indent=2)
    
    logger.info("Model directories initialized")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    download_default_models()
