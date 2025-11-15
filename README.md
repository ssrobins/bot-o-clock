# 🕒 bot-o'clock

### Local, Voice-Driven, Multi-Agent AI Persona Framework

**bot-o'clock** is a fully local, voice-controlled, multi-agent AI system where each agent ("Steve") is an independent persona with its own system prompt, goals, beliefs, memory, voice profile, and LLM context.

## Features

- 🎤 **Voice Input** - Real-time speech recognition with Whisper
- 🗣️ **Voice Cloning** - Unique voice for each agent using Coqui TTS
- 🤖 **Multi-Agent System** - Multiple independent AI personas running simultaneously
- 🧠 **Memory System** - Persistent memory for each agent
- 🔒 **100% Local** - All processing runs offline (STT, LLM, TTS)
- 🎭 **Persona Management** - Customizable agent personalities and behaviors
- 🔊 **Virtual Audio** - Support for BlackHole, Loopback, and other audio routing

## Documentation

- 📖 [Quick Start Guide](QUICKSTART.md) - Get up and running in 5 minutes
- 🔧 [Setup Guide](SETUP.md) - Detailed installation and configuration instructions
- 🏗️ [Architecture](ARCHITECTURE.md) - System design, flow diagrams, and technical details
- 📋 [Project Summary](PROJECT_SUMMARY.md) - Complete overview of what has been built
- 📑 [Project Index](INDEX.md) - Complete file structure and navigation guide
- ✅ [Completion Report](COMPLETION_REPORT.md) - Project status and accomplishments

## Requirements

- Python 3.10+
- macOS (tested) / Linux / Windows
- Ollama (for LLM inference)
- 8GB+ RAM recommended
- 16GB+ for larger models

## Installation

### 1. Install system dependencies

```bash
# macOS
brew install portaudio ffmpeg

# Optional: BlackHole for virtual audio routing
brew install blackhole-2ch
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Install Ollama

```bash
# macOS
brew install ollama

# Start Ollama service
ollama serve
```

### 4. Pull LLM models

```bash
# Recommended models
ollama pull llama3.1:8b
ollama pull llama3.1:70b  # If you have the resources
```

## Quick Start

```bash
# Check your setup
python start.py

# Start bot-o'clock
python src/main.py

# With specific persona
python src/main.py --persona personas/default_steve.yaml

# Multiple agents
python src/main.py --agents steve1,steve2,steve3
```

## Project Structure

```
bot-oclock/
├── src/
│   ├── main.py              # Entry point
│   ├── orchestrator.py      # Multi-agent coordinator
│   ├── steve.py             # Agent implementation
│   ├── audio_input.py       # Audio capture
│   ├── stt.py               # Speech-to-text
│   ├── tts.py               # Text-to-speech
│   └── memory.py            # Memory/storage
├── config/
│   └── settings.yaml        # Global configuration
├── personas/
│   └── *.yaml               # Agent persona definitions
├── voices/
│   └── *.wav                # Voice samples for cloning
└── data/
    └── *.db                 # SQLite databases
```

## Configuration

Edit `config/settings.yaml` to configure:
- Audio devices
- Whisper model size
- Ollama model selection
- TTS settings
- Memory parameters

## Creating a Persona

Create a YAML file in `personas/`:

```yaml
name: "Steve"
system_prompt: "You are a helpful AI assistant..."
voice_sample: "voices/steve.wav"
model: "llama3.1:8b"
temperature: 0.7
goals:
  - "Be helpful"
  - "Stay in character"
beliefs:
  - "Knowledge should be shared"
  - "Privacy is important"
```

## Voice Commands

While running:
- "Create a new Steve named [name]"
- "Switch to Steve [name]"
- "Let [steve1] and [steve2] talk"
- "Exit bot-o'clock"

## Architecture

1. **Audio Input** → Captures microphone/virtual audio
2. **STT (Whisper)** → Converts audio to text
3. **Orchestrator** → Routes messages to agents
4. **Steve Agents** → Process with persona + memory + LLM
5. **TTS (Coqui)** → Generates agent-specific voice
6. **Audio Output** → Plays or routes audio

## License

MIT License - See LICENSE file

## Contributing

Contributions welcome! Please open an issue or PR.

## Credits

Built with:
- [Whisper](https://github.com/openai/whisper)
- [Ollama](https://ollama.ai)
- [Coqui TTS](https://github.com/coqui-ai/TTS)
