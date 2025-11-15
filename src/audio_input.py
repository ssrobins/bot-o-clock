"""
Audio Input Layer for bot-o'clock
Captures audio from microphone, files, or virtual audio devices
"""

import sounddevice as sd
import numpy as np
import queue
import threading
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class AudioConfig:
    """Configuration for audio input"""
    device: Optional[int] = None
    sample_rate: int = 16000
    channels: int = 1
    chunk_size: int = 1024
    dtype: str = 'float32'
    vad_enabled: bool = True
    vad_threshold: float = 0.5


class VoiceActivityDetector:
    """Simple energy-based voice activity detection"""
    
    def __init__(self, threshold: float = 0.5, sample_rate: int = 16000):
        self.threshold = threshold
        self.sample_rate = sample_rate
        self.energy_history = []
        self.history_size = 30
        
    def is_speech(self, audio_chunk: np.ndarray) -> bool:
        """
        Determine if audio chunk contains speech
        
        Args:
            audio_chunk: Audio data as numpy array
            
        Returns:
            True if speech is detected
        """
        # Calculate RMS energy
        energy = np.sqrt(np.mean(audio_chunk ** 2))
        
        # Update history
        self.energy_history.append(energy)
        if len(self.energy_history) > self.history_size:
            self.energy_history.pop(0)
        
        # Adaptive threshold based on recent history
        if len(self.energy_history) >= 10:
            avg_energy = np.mean(self.energy_history)
            adaptive_threshold = avg_energy * self.threshold
        else:
            adaptive_threshold = self.threshold * 0.01
        
        return energy > adaptive_threshold


class AudioInput:
    """
    Handles audio input from various sources
    Supports real-time streaming and voice activity detection
    """
    
    def __init__(self, config: AudioConfig):
        self.config = config
        self.audio_queue = queue.Queue()
        self.is_recording = False
        self.stream = None
        self.vad = None
        
        if config.vad_enabled:
            self.vad = VoiceActivityDetector(
                threshold=config.vad_threshold,
                sample_rate=config.sample_rate
            )
        
        logger.info(f"AudioInput initialized with config: {config}")
    
    def _audio_callback(self, indata, frames, time, status):
        """Callback for sounddevice stream"""
        if status:
            logger.warning(f"Audio callback status: {status}")
        
        # Copy data to avoid issues with buffer reuse
        audio_data = indata.copy()
        
        # Apply VAD if enabled
        if self.vad:
            if self.vad.is_speech(audio_data):
                self.audio_queue.put(audio_data)
        else:
            self.audio_queue.put(audio_data)
    
    def start_recording(self):
        """Start recording audio from input device"""
        if self.is_recording:
            logger.warning("Already recording")
            return
        
        try:
            self.stream = sd.InputStream(
                device=self.config.device,
                channels=self.config.channels,
                samplerate=self.config.sample_rate,
                blocksize=self.config.chunk_size,
                dtype=self.config.dtype,
                callback=self._audio_callback
            )
            self.stream.start()
            self.is_recording = True
            logger.info("Started recording")
        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            raise
    
    def stop_recording(self):
        """Stop recording audio"""
        if not self.is_recording:
            return
        
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        
        self.is_recording = False
        logger.info("Stopped recording")
    
    def get_audio_chunk(self, timeout: float = 1.0) -> Optional[np.ndarray]:
        """
        Get the next audio chunk from the queue
        
        Args:
            timeout: Maximum time to wait for audio chunk
            
        Returns:
            Audio data as numpy array, or None if timeout
        """
        try:
            return self.audio_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def clear_buffer(self):
        """Clear all pending audio from the queue"""
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break
    
    @staticmethod
    def list_devices() -> Dict[int, Dict[str, Any]]:
        """
        List all available audio input devices
        
        Returns:
            Dictionary mapping device index to device info
        """
        devices = {}
        for i, device in enumerate(sd.query_devices()):
            if device['max_input_channels'] > 0:
                devices[i] = {
                    'name': device['name'],
                    'channels': device['max_input_channels'],
                    'sample_rate': device['default_samplerate']
                }
        return devices
    
    @staticmethod
    def get_default_device() -> int:
        """Get the default input device index"""
        return sd.default.device[0]
    
    def __enter__(self):
        """Context manager entry"""
        self.start_recording()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop_recording()


class AudioFileInput:
    """
    Read audio from a file for processing
    Useful for testing or processing pre-recorded audio
    """
    
    def __init__(self, file_path: str, chunk_size: int = 1024):
        self.file_path = file_path
        self.chunk_size = chunk_size
        self.data = None
        self.sample_rate = None
        self.position = 0
    
    def load(self):
        """Load audio file"""
        import soundfile as sf
        self.data, self.sample_rate = sf.read(self.file_path, dtype='float32')
        logger.info(f"Loaded audio file: {self.file_path} ({len(self.data)} samples)")
    
    def get_audio_chunk(self) -> Optional[np.ndarray]:
        """Get next chunk from file"""
        if self.data is None:
            self.load()
        
        if self.position >= len(self.data):
            return None
        
        chunk = self.data[self.position:self.position + self.chunk_size]
        self.position += self.chunk_size
        return chunk
    
    def reset(self):
        """Reset to beginning of file"""
        self.position = 0


if __name__ == "__main__":
    # Test audio input
    logging.basicConfig(level=logging.INFO)
    
    print("Available audio input devices:")
    devices = AudioInput.list_devices()
    for idx, info in devices.items():
        print(f"  [{idx}] {info['name']} - {info['channels']} channels @ {info['sample_rate']} Hz")
    
    print(f"\nDefault input device: {AudioInput.get_default_device()}")
    
    # Test recording
    config = AudioConfig(
        sample_rate=16000,
        channels=1,
        chunk_size=1024,
        vad_enabled=True
    )
    
    print("\nTesting audio input (5 seconds)...")
    with AudioInput(config) as audio_input:
        import time
        chunks_received = 0
        start_time = time.time()
        
        while time.time() - start_time < 5.0:
            chunk = audio_input.get_audio_chunk(timeout=0.5)
            if chunk is not None:
                chunks_received += 1
        
        print(f"Received {chunks_received} audio chunks")
