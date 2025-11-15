# bot-o'clock Quick Start

## Fast Setup (5 minutes)

### Automated Setup (Recommended)
```bash
cd bot-oclock
python setup.py
```

The setup script will handle everything automatically. Or, for manual setup:

### Manual Setup

### 1. Install Ollama & Pull Model
```bash
# Install and start Ollama
brew install ollama
ollama serve &

# Pull a model
ollama pull llama3.1:8b
```

### 2. Install Dependencies
```bash
cd bot-oclock
pip install -r requirements.txt
```

### 3. Run bot-o'clock!
```bash
# Interactive text mode (recommended for first run)
python src/main.py run --mode text
```

## First Interaction

Once running, try:
```
You: Hello!
Steve: [responds]

You: Create a new Steve named Alice
Steve: Created new agent: Alice

You: Switch to Steve Alice
Alice: Switched to Alice

You: Let Steve and Alice talk
[Watch them converse!]
```

## Voice Mode

```bash
# Enable voice input
python src/main.py run --mode voice

# Then just speak!
```

## Common Commands

### Create Custom Agent
```bash
python src/main.py create-persona "MyAgent" --template creative
python src/main.py run --persona personas/myagent.yaml
```

### List Audio Devices
```bash
python src/main.py devices
```

### Check Status
```bash
python src/main.py status
```

## Voice Commands

While running, say:
- "Create a new Steve named [name]"
- "Switch to Steve [name]"
- "List agents"
- "Let [agent1] and [agent2] talk"
- "Help"
- "Exit bot-o'clock"

## Tips

1. **First time?** Run `python start.py` to check your setup, or start with text mode to understand the system
2. **Want multiple agents?** Load multiple personas:
   ```bash
   python src/main.py run \
     --persona personas/default_steve.yaml \
     --persona personas/alice_assistant.yaml \
     --mode text
   ```
3. **Need voice cloning?** See SETUP.md for voice sample instructions
4. **Errors?** Check that Ollama is running: `curl http://localhost:11434/api/tags`

## Example Session

```bash
$ python src/main.py run --mode text

🕒 bot-o'clock
Local Voice-Driven Multi-Agent AI Framework

Initializing components...
✓ Memory store initialized
✓ Connected to Ollama
✓ Speech-to-text loaded (Whisper base)
✓ Text-to-speech loaded (Coqui TTS)
✓ Orchestrator initialized
✓ Audio input configured

You: What's your name?
Steve: My name is Steve! I'm a helpful AI assistant. How can I help you today?

You: Create a new Steve named Max with a creative personality
Steve: Created new agent: Max

You: Switch to Steve Max
Max: Switched to Max

You: Tell me a creative story idea
Max: Oh, I love this! Imagine a world where dreams are tangible objects...
```

## Need More Help?

- See **SETUP.md** for detailed installation
- See **README.md** for full documentation
- Check individual module files for component testing
