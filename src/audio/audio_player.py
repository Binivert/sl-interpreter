"""Audio playback utilities."""

import io
import logging
import wave
from typing import Optional

logger = logging.getLogger(__name__)


class AudioPlayer:
    """Plays audio data."""
    
    def __init__(self):
        self._pyaudio = None
        self._stream = None
    
    def play(self, audio_data: bytes):
        """Play WAV audio data."""
        
        try:
            import pyaudio
            
            if self._pyaudio is None:
                self._pyaudio = pyaudio.PyAudio()
            
            # Parse WAV data
            wav_io = io.BytesIO(audio_data)
            with wave.open(wav_io, 'rb') as wav_file:
                # Open stream
                stream = self._pyaudio.open(
                    format=self._pyaudio.get_format_from_width(wav_file.getsampwidth()),
                    channels=wav_file.getnchannels(),
                    rate=wav_file.getframerate(),
                    output=True
                )
                
                # Play audio
                chunk_size = 1024
                data = wav_file.readframes(chunk_size)
                
                while data:
                    stream.write(data)
                    data = wav_file.readframes(chunk_size)
                
                stream.stop_stream()
                stream.close()
                
        except ImportError:
            logger.warning("PyAudio not installed, cannot play audio")
        except Exception as e:
            logger.error(f"Error playing audio: {e}")
    
    def close(self):
        """Clean up resources."""
        
        if self._pyaudio:
            self._pyaudio.terminate()
            self._pyaudio = None
