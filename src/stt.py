"""
Speech-to-Text Layer for bot-o'clock
Uses Whisper for local audio transcription
Supports both streaming and batch processing
"""

import numpy as np
import asyncio
import logging
from typing import Optional, List, Union
from dataclasses import dataclass
import threading
import queue

logger = logging.getLogger(__name__)


@dataclass
class STTConfig:
    """Configuration for speech-to-text"""
    model_size: str = "base"  # tiny, base, small, medium, large
    language: str = "en"
    device: str = "cpu"
    compute_type: str = "int8"
    beam_size: int = 5
    vad_filter: bool = True


class WhisperSTT:
    """
    Speech-to-Text using faster-whisper
    Supports both synchronous and asynchronous interfaces
    """
    
    def __init__(self, config: STTConfig):
        self.config = config
        self.model = None
        self._load_model()
        
    def _load_model(self):
        """Load the Whisper model"""
        try:
            from faster_whisper import WhisperModel
            
            logger.info(f"Loading Whisper model: {self.config.model_size}")
            self.model = WhisperModel(
                self.config.model_size,
                device=self.config.device,
                compute_type=self.config.compute_type
            )
            logger.info("Whisper model loaded successfully")
            
        except ImportError:
            logger.error("faster-whisper not installed. Install with: pip install faster-whisper")
            raise
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise
    
    def transcribe(self, audio_data: Union[np.ndarray, str]) -> str:
        """
        Transcribe audio to text (synchronous)
        
        Args:
            audio_data: Either numpy array of audio samples or path to audio file
            
        Returns:
            Transcribed text
        """
        try:
            # If audio_data is a file path
            if isinstance(audio_data, str):
                segments, info = self.model.transcribe(
                    audio_data,
                    language=self.config.language,
                    beam_size=self.config.beam_size,
                    vad_filter=self.config.vad_filter
                )
            else:
                # If audio_data is numpy array
                # Ensure it's float32 and in the right range
                if audio_data.dtype != np.float32:
                    audio_data = audio_data.astype(np.float32)
                
                segments, info = self.model.transcribe(
                    audio_data,
                    language=self.config.language,
                    beam_size=self.config.beam_size,
                    vad_filter=self.config.vad_filter
                )
            
            # Combine all segments
            text = " ".join([segment.text for segment in segments])
            
            logger.debug(f"Transcribed: {text}")
            return text.strip()
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return ""
    
    async def transcribe_async(self, audio_data: Union[np.ndarray, str]) -> str:
        """
        Transcribe audio to text (asynchronous)
        
        Args:
            audio_data: Either numpy array of audio samples or path to audio file
            
        Returns:
            Transcribed text
        """
        # Run transcription in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.transcribe, audio_data)
    
    def transcribe_stream(
        self,
        audio_chunks: List[np.ndarray],
        min_silence_duration: float = 0.5
    ) -> str:
        """
        Transcribe a stream of audio chunks
        
        Args:
            audio_chunks: List of audio data chunks
            min_silence_duration: Minimum silence duration to consider end of speech
            
        Returns:
            Transcribed text
        """
        if not audio_chunks:
            return ""
        
        # Concatenate all chunks
        audio_data = np.concatenate(audio_chunks)
        return self.transcribe(audio_data)


class StreamingTranscriber:
    """
    Handles real-time streaming transcription
    Buffers audio and transcribes on silence detection or buffer full
    """
    
    def __init__(
        self,
        stt: WhisperSTT,
        buffer_duration: float = 3.0,
        sample_rate: int = 16000,
        callback: Optional[callable] = None
    ):
        self.stt = stt
        self.buffer_duration = buffer_duration
        self.sample_rate = sample_rate
        self.callback = callback
        
        self.buffer = []
        self.max_buffer_size = int(buffer_duration * sample_rate)
        self.is_running = False
        self.thread = None
        self.audio_queue = queue.Queue()
        
    def add_audio(self, audio_chunk: np.ndarray):
        """Add audio chunk to the streaming buffer"""
        if self.is_running:
            self.audio_queue.put(audio_chunk)
    
    def _process_loop(self):
        """Background processing loop"""
        while self.is_running:
            try:
                chunk = self.audio_queue.get(timeout=0.1)
                self.buffer.append(chunk)
                
                # Check if buffer is full
                total_samples = sum(len(c) for c in self.buffer)
                if total_samples >= self.max_buffer_size:
                    self._transcribe_buffer()
                    
            except queue.Empty:
                # Transcribe if buffer has data and queue is empty
                if self.buffer:
                    self._transcribe_buffer()
            except Exception as e:
                logger.error(f"Error in streaming transcriber: {e}")
    
    def _transcribe_buffer(self):
        """Transcribe current buffer and clear it"""
        if not self.buffer:
            return
        
        try:
            audio_data = np.concatenate(self.buffer)
            text = self.stt.transcribe(audio_data)
            
            if text and self.callback:
                self.callback(text)
            
            self.buffer.clear()
            
        except Exception as e:
            logger.error(f"Failed to transcribe buffer: {e}")
            self.buffer.clear()
    
    def start(self):
        """Start streaming transcription"""
        if self.is_running:
            return
        
        self.is_running = True
        self.thread = threading.Thread(target=self._process_loop, daemon=True)
        self.thread.start()
        logger.info("Streaming transcriber started")
    
    def stop(self):
        """Stop streaming transcription"""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        
        # Process any remaining buffer
        self._transcribe_buffer()
        logger.info("Streaming transcriber stopped")


class WhisperSTTFallback:
    """
    Fallback to openai-whisper if faster-whisper is not available
    """
    
    def __init__(self, config: STTConfig):
        self.config = config
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the Whisper model using openai-whisper"""
        try:
            import whisper
            
            logger.info(f"Loading Whisper model (openai-whisper): {self.config.model_size}")
            self.model = whisper.load_model(self.config.model_size, device=self.config.device)
            logger.info("Whisper model loaded successfully")
            
        except ImportError:
            logger.error("openai-whisper not installed. Install with: pip install openai-whisper")
            raise
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise
    
    def transcribe(self, audio_data: Union[np.ndarray, str]) -> str:
        """Transcribe audio using openai-whisper"""
        try:
            result = self.model.transcribe(
                audio_data,
                language=self.config.language,
                fp16=(self.config.compute_type == "float16")
            )
            text = result['text'].strip()
            logger.debug(f"Transcribed: {text}")
            return text
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return ""
    
    async def transcribe_async(self, audio_data: Union[np.ndarray, str]) -> str:
        """Async transcription"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.transcribe, audio_data)


def create_stt(config: STTConfig, prefer_faster: bool = True) -> Union[WhisperSTT, WhisperSTTFallback]:
    """
    Factory function to create STT instance
    
    Args:
        config: STT configuration
        prefer_faster: Try faster-whisper first, fallback to openai-whisper
        
    Returns:
        STT instance
    """
    if prefer_faster:
        try:
            return WhisperSTT(config)
        except Exception as e:
            logger.warning(f"Failed to load faster-whisper, trying openai-whisper: {e}")
            return WhisperSTTFallback(config)
    else:
        return WhisperSTTFallback(config)


if __name__ == "__main__":
    # Test STT
    logging.basicConfig(level=logging.INFO)
    
    config = STTConfig(
        model_size="base",
        language="en",
        device="cpu"
    )
    
    print("Loading Whisper model...")
    stt = create_stt(config)
    
    print("STT ready. Model loaded successfully!")
    print(f"Using model: {config.model_size}")
    print(f"Device: {config.device}")
    
    # Test with a sample if available
    # For real testing, you would need an actual audio file
    print("\nTo test transcription, provide an audio file path or numpy array")
