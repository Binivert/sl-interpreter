"""Text-to-speech engine abstraction."""

import logging
import subprocess
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class TTSEngine(ABC):
    """Abstract base class for TTS engines."""
    
    def __init__(self, config: dict):
        self.config = config
        self.current_voice: str = ""
        self.rate: float = 1.0
        self.pitch: float = 1.0
    
    @abstractmethod
    def synthesize(self, text: str) -> bytes:
        """Synthesize text to audio.
        
        Returns:
            WAV audio data as bytes.
        """
        pass
    
    @abstractmethod
    def set_voice(self, voice_id: str):
        """Set the voice to use."""
        pass
    
    @abstractmethod
    def list_voices(self) -> List[Dict[str, str]]:
        """List available voices."""
        pass
    
    def set_rate(self, rate: float):
        """Set speech rate (0.5 to 2.0)."""
        self.rate = max(0.5, min(2.0, rate))
    
    def set_pitch(self, pitch: float):
        """Set speech pitch (0.5 to 2.0)."""
        self.pitch = max(0.5, min(2.0, pitch))


class PiperTTSEngine(TTSEngine):
    """Piper TTS engine for natural-sounding speech."""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.models_dir = Path(config.get("models_dir", "models/voices"))
        self.model_path: Optional[Path] = None
        self.config_path: Optional[Path] = None
        
        # Set default voice
        default_voice = config.get("voice", "en_amy")
        if self._voice_exists(default_voice):
            self.set_voice(default_voice)
    
    def synthesize(self, text: str) -> bytes:
        """Synthesize text using Piper."""
        
        if not self.model_path:
            raise RuntimeError("No voice model loaded")
        
        try:
            from piper import PiperVoice
            
            voice = PiperVoice.load(str(self.model_path))
            
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                temp_path = f.name
            
            # Synthesize to file
            with open(temp_path, "wb") as wav_file:
                voice.synthesize(text, wav_file)
            
            # Read and return
            with open(temp_path, "rb") as f:
                audio_data = f.read()
            
            Path(temp_path).unlink()
            
            return audio_data
            
        except ImportError:
            logger.warning("Piper not available, falling back to espeak")
            return self._fallback_espeak(text)
    
    def _fallback_espeak(self, text: str) -> bytes:
        """Fallback to espeak if Piper unavailable."""
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_path = f.name
        
        try:
            subprocess.run(
                ["espeak", "-w", temp_path, text],
                check=True,
                capture_output=True
            )
            
            with open(temp_path, "rb") as f:
                audio_data = f.read()
            
            return audio_data
            
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def set_voice(self, voice_id: str):
        """Set the Piper voice model."""
        
        voice_dir = self.models_dir / voice_id
        
        if not voice_dir.exists():
            raise FileNotFoundError(f"Voice not found: {voice_id}")
        
        # Find model file
        model_files = list(voice_dir.glob("*.onnx"))
        if not model_files:
            raise FileNotFoundError(f"No model file in {voice_dir}")
        
        self.model_path = model_files[0]
        self.config_path = voice_dir / "config.json"
        self.current_voice = voice_id
        
        logger.info(f"Voice set to: {voice_id}")
    
    def list_voices(self) -> List[Dict[str, str]]:
        """List available Piper voices."""
        
        voices = []
        
        if not self.models_dir.exists():
            return voices
        
        for voice_dir in self.models_dir.iterdir():
            if voice_dir.is_dir():
                model_files = list(voice_dir.glob("*.onnx"))
                if model_files:
                    voices.append({
                        "id": voice_dir.name,
                        "name": voice_dir.name.replace("_", " ").title(),
                        "path": str(voice_dir)
                    })
        
        return voices
    
    def _voice_exists(self, voice_id: str) -> bool:
        """Check if a voice exists."""
        
        voice_dir = self.models_dir / voice_id
        return voice_dir.exists() and list(voice_dir.glob("*.onnx"))


class CoquiTTSEngine(TTSEngine):
    """Coqui TTS engine."""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.model_name = config.get("model", "tts_models/en/ljspeech/tacotron2-DDC")
        self.tts = None
        self._init_model()
    
    def _init_model(self):
        """Initialize the TTS model."""
        
        try:
            from TTS.api import TTS
            self.tts = TTS(model_name=self.model_name)
            self.current_voice = self.model_name
            logger.info(f"Coqui TTS initialized: {self.model_name}")
        except ImportError:
            logger.warning("Coqui TTS not installed")
        except Exception as e:
            logger.error(f"Failed to initialize Coqui TTS: {e}")
    
    def synthesize(self, text: str) -> bytes:
        """Synthesize text using Coqui TTS."""
        
        if self.tts is None:
            raise RuntimeError("Coqui TTS not initialized")
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_path = f.name
        
        try:
            self.tts.tts_to_file(text=text, file_path=temp_path)
            
            with open(temp_path, "rb") as f:
                audio_data = f.read()
            
            return audio_data
            
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def set_voice(self, voice_id: str):
        """Set the Coqui model."""
        
        self.model_name = voice_id
        self._init_model()
    
    def list_voices(self) -> List[Dict[str, str]]:
        """List available Coqui models."""
        
        # Return common models
        return [
            {"id": "tts_models/en/ljspeech/tacotron2-DDC", "name": "LJSpeech Tacotron2"},
            {"id": "tts_models/en/ljspeech/vits", "name": "LJSpeech VITS"},
            {"id": "tts_models/en/vctk/vits", "name": "VCTK VITS Multi-speaker"},
        ]


class TTSEngineFactory:
    """Factory for creating TTS engines."""
    
    @staticmethod
    def create(config: dict) -> TTSEngine:
        """Create a TTS engine based on configuration."""
        
        engine_type = config.get("engine", "piper")
        
        if engine_type == "piper":
            return PiperTTSEngine(config)
        elif engine_type == "coqui":
            return CoquiTTSEngine(config)
        else:
            logger.warning(f"Unknown TTS engine: {engine_type}, using Piper")
            return PiperTTSEngine(config)
