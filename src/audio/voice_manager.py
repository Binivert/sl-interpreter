"""Voice model management."""

import json
import logging
import shutil
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class VoiceManager:
    """Manages voice models."""
    
    PIPER_VOICES_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main"
    
    def __init__(self, voices_dir: Path):
        self.voices_dir = voices_dir
        self.voices_dir.mkdir(parents=True, exist_ok=True)
    
    def list_installed(self) -> List[Dict[str, str]]:
        """List installed voice models."""
        
        voices = []
        
        for voice_dir in self.voices_dir.iterdir():
            if voice_dir.is_dir():
                config_path = voice_dir / "config.json"
                
                voice_info = {
                    "id": voice_dir.name,
                    "path": str(voice_dir)
                }
                
                if config_path.exists():
                    with open(config_path) as f:
                        config = json.load(f)
                    voice_info["language"] = config.get("language", {}).get("name_english", "Unknown")
                    voice_info["quality"] = config.get("quality", "medium")
                
                voices.append(voice_info)
        
        return voices
    
    def download_voice(self, voice_name: str, language: str = "en") -> Path:
        """Download a Piper voice model."""
        
        voice_dir = self.voices_dir / voice_name
        voice_dir.mkdir(exist_ok=True)
        
        # Construct URLs
        base_url = f"{self.PIPER_VOICES_URL}/{language}/{voice_name}"
        model_url = f"{base_url}/{voice_name}.onnx"
        config_url = f"{base_url}/{voice_name}.onnx.json"
        
        # Download model
        model_path = voice_dir / f"{voice_name}.onnx"
        if not model_path.exists():
            logger.info(f"Downloading {model_url}")
            urllib.request.urlretrieve(model_url, model_path)
        
        # Download config
        config_path = voice_dir / "config.json"
        if not config_path.exists():
            logger.info(f"Downloading {config_url}")
            urllib.request.urlretrieve(config_url, config_path)
        
        logger.info(f"Voice downloaded: {voice_name}")
        
        return voice_dir
    
    def delete_voice(self, voice_name: str):
        """Delete an installed voice."""
        
        voice_dir = self.voices_dir / voice_name
        
        if voice_dir.exists():
            shutil.rmtree(voice_dir)
            logger.info(f"Voice deleted: {voice_name}")
