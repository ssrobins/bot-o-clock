# bot-o'clock Setup Guide

## Platform Support

- ✅ **macOS**: Fully supported and tested with automated setup script
- ⚠️ **Linux**: Potentially compatible but untested - manual installation required
- ⚠️ **Windows**: Potentially compatible but untested - manual installation required

## Quick Setup (macOS only)

**Recommended for macOS users:** Use the automated setup script:

```bash
python setup.py
```

This will guide you through all installation steps automatically.

## Manual Setup

For Linux/Windows or manual installation on macOS, follow the detailed steps below.

## Prerequisites

1. **Python 3.10-3.12**
   ```bash
   python --version  # Should be 3.10, 3.11, or 3.12 (not 3.13+)
   ```
   
   **Note:** Python 3.13+ is not yet supported due to TTS library compatibility.
   If you have Python 3.13, install Python 3.12:
   ```bash
   brew install python@3.12
   ```

2. **Package Manager**
   - **macOS**: Homebrew
     ```bash
     /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
     ```
   - **Linux**: apt, yum, or your distribution's package manager
   - **Windows**: See individual tool documentation

## Installation Steps

### 1. Install System Dependencies

**macOS:**
```bash
# Audio libraries
brew install portaudio ffmpeg

# Optional: BlackHole for virtual audio routing
brew install blackhole-2ch
```

**Linux (Ubuntu/Debian):**
```bash
# Audio libraries
sudo apt-get update
sudo apt-get install portaudio19-dev ffmpeg

# For CUDA support (optional)
# Follow NVIDIA CUDA installation guide
```

**Linux (Fedora/RHEL):**
```bash
# Audio libraries
sudo dnf install portaudio-devel ffmpeg
```

**Windows:**
```powershell
# Install via package manager or download binaries:
# - PortAudio: http://www.portaudio.com/
# - FFmpeg: https://ffmpeg.org/download.html
# Or use chocolatey:
choco install ffmpeg
```

### 2. Create Python Virtual Environment

```bash
cd bot-oclock
python -m venv venv

# Activate the virtual environment:
# macOS/Linux:
source venv/bin/activate
# Windows:
# venv\Scripts\activate
```

### 3. Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Note:** Some dependencies may take time to install:
- TTS (Coqui) downloads models on first use
- faster-whisper downloads models on first use

### 4. Install and Setup Ollama

**macOS:**
```bash
# Install Ollama
brew install ollama

# Start Ollama service (in a separate terminal)
ollama serve
```

**Linux:**
```bash
# Download and install
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama service
ollama serve
```

**Windows:**
- Download installer from https://ollama.com/download
- Run the installer
- Ollama will start automatically as a service

**Pull Models (all platforms):**

In another terminal, pull models:

```bash
# Recommended models
ollama pull llama3.1:8b       # Fast, good quality
ollama pull llama3.1:70b      # Better quality, needs more resources
ollama pull qwen2.5:7b        # Alternative, good performance

# List installed models
ollama list
```

### 5. Test Installation

```bash
# Test audio devices
python src/main.py devices

# Test in interactive mode
python src/main.py run --mode text

# Test with default persona
python src/main.py run --persona personas/default_steve.yaml --mode text
```

## Configuration

### Audio Configuration

Edit `config/settings.yaml` to configure audio devices:

```yaml
audio:
  input_device: null   # null = default, or device index
  output_device: null
  sample_rate: 16000
  vad_enabled: true
```

To find device indices:
```bash
python src/main.py devices
```

### Model Configuration

```yaml
# STT Model (Whisper)
stt:
  model: "base"  # Options: tiny, base, small, medium, large

# LLM Model (Ollama)
llm:
  default_model: "llama3.1:8b"

# TTS Model (Coqui)
tts:
  model: "tts_models/multilingual/multi-dataset/xtts_v2"
```

### Model Size Guide

**Whisper (STT):**
- `tiny`: ~75MB, fastest, less accurate
- `base`: ~150MB, good balance (recommended)
- `small`: ~500MB, better accuracy
- `medium`: ~1.5GB, very accurate
- `large`: ~3GB, best accuracy

**LLaMA (LLM):**
- `7B`: 4-8GB RAM, fast
- `13B`: 8-16GB RAM, better quality
- `70B`: 48GB+ RAM, best quality

## Usage Examples

### Text Mode (Interactive)

```bash
# Start with default agent
python src/main.py run --mode text

# Start with specific persona
python src/main.py run --persona personas/alice_assistant.yaml --mode text

# Load multiple agents
python src/main.py run \
  --persona personas/default_steve.yaml \
  --persona personas/max_creative.yaml \
  --mode text
```

### Voice Mode

```bash
# Start with voice input
python src/main.py run --mode voice

# With specific persona
python src/main.py run --persona personas/default_steve.yaml --mode voice
```

### Voice Commands

While running, you can use:
- "Create a new Steve named Alice"
- "Switch to Steve Alice"
- "List agents"
- "Let Steve and Alice talk"
- "Help"
- "Exit bot-o'clock"

### Creating Personas

```bash
# Create from template
python src/main.py create-persona "MySteve" --template default

# Templates: default, assistant, creative
python src/main.py create-persona "Assistant" --template assistant
python src/main.py create-persona "Creative" --template creative
```

Edit the generated YAML file in `personas/` to customize.

## Adding Voice Cloning

1. Record a clean audio sample (10-30 seconds) of the target voice
2. Save as WAV file in `voices/` directory
3. Update persona YAML:

```yaml
name: "Steve"
voice_sample: "voices/steve.wav"
voice_language: "en"
```

## Troubleshooting

### Ollama Connection Failed

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama
ollama serve

# Check logs
tail -f ~/.ollama/logs/server.log
```

### Audio Issues

```bash
# List devices
python src/main.py devices

# Test audio input
python src/audio_input.py

# Check permissions (macOS)
# System Preferences > Security & Privacy > Microphone
```

### TTS Not Working

```bash
# Test TTS installation
python -c "from TTS.api import TTS; print('TTS OK')"

# Reinstall if needed
pip uninstall TTS
pip install TTS
```

### Whisper Model Download

Models download automatically on first use. To pre-download:

```bash
python -c "from faster_whisper import WhisperModel; WhisperModel('base')"
```

## Performance Tips

1. **Use appropriate model sizes** for your hardware
2. **Enable GPU** if available (CUDA):
   ```yaml
   stt:
     device: "cuda"
   tts:
     device: "cuda"
   ```
3. **Reduce context window** for faster responses:
   ```yaml
   llm:
     context_window: 2048
   ```
4. **Use VAD** to reduce unnecessary processing:
   ```yaml
   audio:
     vad_enabled: true
   ```

## Next Steps

1. Create custom personas
2. Record voice samples for cloning
3. Experiment with different models
4. Set up virtual audio routing for complex setups
5. Explore inter-agent conversations

## Support

For issues and questions:
- Check the main README.md
- Review the design document
- Inspect log files in `data/bot-oclock.log`
- Test individual components (each module has a `__main__` section)
