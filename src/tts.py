"""
Text-to-Speech Layer for bot-o'clock
Uses Coqui TTS with XTTS v2 for voice cloning
"""

import numpy as np
import logging
from typing import Optional, Union
from dataclasses import dataclass
import os
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class TTSConfig:
    """Configuration for text-to-speech"""
    model_name: str = "tts_models/multilingual/multi-dataset/xtts_v2"
    language: str = "en"
    device: str = "cpu"
    speed: float = 1.0
    use_gpu: bool = False


class CoquiTTS:
    """
    Text-to-Speech using Coqui TTS (XTTS v2)
    Supports voice cloning from audio samples
    """
    
    def __init__(self, config: TTSConfig):
        self.config = config
        self.tts = None
        self._load_model()
    
    def _load_model(self):
        """Load the TTS model"""
        try:
            from TTS.api import TTS
            import torch
            
            # Fix for PyTorch 2.6+ weights_only default change
            # Allow TTS classes to be loaded safely
            try:
                from TTS.tts.configs.xtts_config import XttsConfig
                torch.serialization.add_safe_globals([XttsConfig])
            except Exception:
                pass  # Older PyTorch or TTS versions don't need this
            
            logger.info(f"Loading TTS model: {self.config.model_name}")
            
            # Initialize TTS
            self.tts = TTS(
                model_name=self.config.model_name,
                progress_bar=False,
                gpu=self.config.use_gpu
            )
            
            logger.info("TTS model loaded successfully")
            
        except ImportError:
            logger.error("TTS library not installed. Install with: pip install TTS")
            raise
        except Exception as e:
            logger.error(f"Failed to load TTS model: {e}")
            raise
    
    def synthesize(
        self,
        text: str,
        speaker_wav: Optional[str] = None,
        output_path: Optional[str] = None,
        language: Optional[str] = None
    ) -> Union[str, np.ndarray]:
        """
        Synthesize speech from text
        
        Args:
            text: Text to synthesize
            speaker_wav: Path to speaker voice sample for cloning (optional)
            output_path: Path to save output WAV file (optional)
            language: Language code (optional, uses config default)
            
        Returns:
            If output_path is provided: path to saved file
            Otherwise: numpy array of audio samples
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for synthesis")
            return None
        
        try:
            lang = language or self.config.language
            
            # If no output path, create temp file
            temp_file = None
            if output_path is None:
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
                output_path = temp_file.name
                temp_file.close()
            
            # Synthesize with voice cloning if speaker_wav provided
            if speaker_wav and os.path.exists(speaker_wav):
                logger.debug(f"Synthesizing with voice clone: {speaker_wav}")
                self.tts.tts_to_file(
                    text=text,
                    speaker_wav=speaker_wav,
                    language=lang,
                    file_path=output_path,
                    speed=self.config.speed
                )
            else:
                # Use default voice
                logger.debug("Synthesizing with default voice")
                self.tts.tts_to_file(
                    text=text,
                    language=lang,
                    file_path=output_path,
                    speed=self.config.speed
                )
            
            logger.info(f"Synthesized audio saved to: {output_path}")
            
            # If temporary file, read and return as numpy array
            if temp_file:
                import soundfile as sf
                audio, sample_rate = sf.read(output_path)
                os.unlink(output_path)  # Clean up temp file
                return audio
            
            return output_path
            
        except Exception as e:
            logger.error(f"Speech synthesis failed: {e}")
            if temp_file and os.path.exists(output_path):
                os.unlink(output_path)
            return None
    
    def synthesize_streaming(
        self,
        text: str,
        speaker_wav: Optional[str] = None,
        chunk_size: int = 4096
    ):
        """
        Synthesize speech in streaming chunks (future implementation)
        
        Args:
            text: Text to synthesize
            speaker_wav: Path to speaker voice sample
            chunk_size: Size of audio chunks to yield
            
        Yields:
            Audio chunks as numpy arrays
        """
        # For now, synthesize full audio and chunk it
        audio = self.synthesize(text, speaker_wav)
        
        if isinstance(audio, np.ndarray):
            for i in range(0, len(audio), chunk_size):
                yield audio[i:i + chunk_size]
    
    def clone_voice(
        self,
        text: str,
        reference_audio: str,
        output_path: str,
        language: Optional[str] = None
    ) -> str:
        """
        Clone a voice from reference audio and synthesize text
        
        Args:
            text: Text to synthesize
            reference_audio: Path to reference audio file for voice cloning
            output_path: Path to save output
            language: Language code
            
        Returns:
            Path to synthesized audio file
        """
        if not os.path.exists(reference_audio):
            logger.error(f"Reference audio not found: {reference_audio}")
            return None
        
        return self.synthesize(
            text=text,
            speaker_wav=reference_audio,
            output_path=output_path,
            language=language
        )


class AudioOutput:
    """
    Handle audio output playback
    Supports playing to default device or routing to virtual devices
    """
    
    def __init__(self, device: Optional[int] = None, sample_rate: int = 22050):
        self.device = device
        self.sample_rate = sample_rate
    
    def play(self, audio_data: Union[str, np.ndarray]):
        """
        Play audio
        
        Args:
            audio_data: Either path to WAV file or numpy array
        """
        try:
            import sounddevice as sd
            import soundfile as sf
            
            # Load audio if it's a file path
            if isinstance(audio_data, str):
                audio_data, sample_rate = sf.read(audio_data)
            else:
                sample_rate = self.sample_rate
            
            # Play audio
            sd.play(audio_data, sample_rate, device=self.device)
            sd.wait()
            
        except Exception as e:
            logger.error(f"Failed to play audio: {e}")
    
    async def play_async(self, audio_data: Union[str, np.ndarray]):
        """Play audio asynchronously"""
        import asyncio
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.play, audio_data)
    
    @staticmethod
    def list_output_devices():
        """List available audio output devices"""
        import sounddevice as sd
        devices = {}
        for i, device in enumerate(sd.query_devices()):
            if device['max_output_channels'] > 0:
                devices[i] = {
                    'name': device['name'],
                    'channels': device['max_output_channels'],
                    'sample_rate': device['default_samplerate']
                }
        return devices


class VoiceProfile:
    """
    Represents a voice profile for an agent
    Stores reference audio and voice characteristics
    """
    
    def __init__(
        self,
        name: str,
        reference_audio: str,
        language: str = "en",
        description: Optional[str] = None
    ):
        self.name = name
        self.reference_audio = reference_audio
        self.language = language
        self.description = description
        
        if not os.path.exists(reference_audio):
            logger.warning(f"Reference audio not found: {reference_audio}")
    
    def validate(self) -> bool:
        """Check if voice profile is valid"""
        return os.path.exists(self.reference_audio)
    
    @staticmethod
    def from_dict(data: dict) -> 'VoiceProfile':
        """Create VoiceProfile from dictionary"""
        return VoiceProfile(
            name=data['name'],
            reference_audio=data['reference_audio'],
            language=data.get('language', 'en'),
            description=data.get('description')
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'reference_audio': self.reference_audio,
            'language': self.language,
            'description': self.description
        }


class TTSManager:
    """
    Manages multiple TTS voices and profiles
    """
    
    def __init__(self, config: TTSConfig):
        self.config = config
        self.tts = CoquiTTS(config)
        self.voice_profiles = {}
    
    def add_voice_profile(self, profile: VoiceProfile):
        """Add a voice profile"""
        if profile.validate():
            self.voice_profiles[profile.name] = profile
            logger.info(f"Added voice profile: {profile.name}")
        else:
            logger.error(f"Invalid voice profile: {profile.name}")
    
    def remove_voice_profile(self, name: str):
        """Remove a voice profile"""
        if name in self.voice_profiles:
            del self.voice_profiles[name]
            logger.info(f"Removed voice profile: {name}")
    
    def get_voice_profile(self, name: str) -> Optional[VoiceProfile]:
        """Get a voice profile by name"""
        return self.voice_profiles.get(name)
    
    def synthesize_with_profile(
        self,
        text: str,
        profile_name: str,
        output_path: Optional[str] = None
    ) -> Union[str, np.ndarray]:
        """
        Synthesize speech using a voice profile
        
        Args:
            text: Text to synthesize
            profile_name: Name of voice profile
            output_path: Optional output path
            
        Returns:
            Audio data or path to file
        """
        profile = self.get_voice_profile(profile_name)
        if not profile:
            logger.error(f"Voice profile not found: {profile_name}")
            return None
        
        return self.tts.synthesize(
            text=text,
            speaker_wav=profile.reference_audio,
            output_path=output_path,
            language=profile.language
        )


if __name__ == "__main__":
    # Test TTS
    logging.basicConfig(level=logging.INFO)
    
    print("Testing TTS system...")
    
    config = TTSConfig(
        model_name="tts_models/en/ljspeech/tacotron2-DDC",
        language="en",
        device="cpu"
    )
    
    print("Available output devices:")
    devices = AudioOutput.list_output_devices()
    for idx, info in devices.items():
        print(f"  [{idx}] {info['name']} - {info['channels']} channels")
    
    print("\nTTS initialized. Ready to synthesize speech!")
    print("Note: To test voice cloning, provide a reference audio file")
