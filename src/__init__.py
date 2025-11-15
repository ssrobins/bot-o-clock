"""
bot-o'clock - Local Voice-Driven Multi-Agent AI Framework

A fully local, voice-controlled, multi-agent AI system where each agent
has its own persona, memory, voice, and LLM context.
"""

__version__ = "1.0.0"
__author__ = "bot-o'clock Contributors"

from .audio_input import AudioInput, AudioConfig, VoiceActivityDetector
from .stt import WhisperSTT, STTConfig, StreamingTranscriber, create_stt
from .tts import CoquiTTS, TTSConfig, AudioOutput, VoiceProfile, TTSManager
from .memory import MemoryStore, Message, Conversation
from .steve import Steve, PersonaConfig, LLMClient, SteveFactory
from .orchestrator import Orchestrator, VoiceCommandParser, AudioRoute

__all__ = [
    # Audio
    'AudioInput',
    'AudioConfig',
    'VoiceActivityDetector',
    'AudioOutput',
    
    # STT
    'WhisperSTT',
    'STTConfig',
    'StreamingTranscriber',
    'create_stt',
    
    # TTS
    'CoquiTTS',
    'TTSConfig',
    'VoiceProfile',
    'TTSManager',
    
    # Memory
    'MemoryStore',
    'Message',
    'Conversation',
    
    # Agents
    'Steve',
    'PersonaConfig',
    'LLMClient',
    'SteveFactory',
    
    # Orchestrator
    'Orchestrator',
    'VoiceCommandParser',
    'AudioRoute',
]
