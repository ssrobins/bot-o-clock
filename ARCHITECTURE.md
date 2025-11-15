# 🕒 bot-o'clock - Complete Architecture

## System Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           USER INTERACTION                               │
│                                                                          │
│    🎤 Microphone Input          💬 Text Input          🔊 Voice Output   │
└────────┬──────────────────────────────┬──────────────────────┬──────────┘
         │                               │                      │
         ▼                               ▼                      ▼
┌────────────────────┐         ┌────────────────────┐  ┌────────────────┐
│  audio_input.py    │         │     main.py        │  │    tts.py      │
│                    │         │   (CLI Interface)  │  │                │
│ - AudioInput       │         │                    │  │ - CoquiTTS     │
│ - VAD              │         │ - Interactive Mode │  │ - VoiceProfile │
│ - Device Config    │         │ - Voice Mode       │  │ - AudioOutput  │
└─────────┬──────────┘         │ - Commands         │  └───────▲────────┘
          │                    └──────────┬─────────┘          │
          │                               │                    │
          ▼                               ▼                    │
┌────────────────────┐         ┌─────────────────────────────────────────┐
│     stt.py         │         │        orchestrator.py                  │
│                    │         │                                         │
│ - WhisperSTT       │────────▶│  ┌────────────────────────────────┐    │
│ - Streaming        │         │  │   ORCHESTRATOR CORE            │    │
│ - Model Config     │         │  │                                │    │
└────────────────────┘         │  │ - Agent Management             │    │
                               │  │ - Voice Command Parsing        │    │
                               │  │ - Audio Routing                │    │
                               │  │ - Inter-Agent Communication    │    │
                               │  └────────────┬───────────────────┘    │
                               │               │                         │
                               │  ┌────────────▼───────────────────┐    │
                               │  │    Active Agents Registry      │    │
                               │  │  ┌───────┐ ┌───────┐ ┌───────┐│    │
                               │  │  │Steve 1│ │Steve 2│ │Steve N││    │
                               │  │  └───┬───┘ └───┬───┘ └───┬───┘│    │
                               │  └──────┼─────────┼─────────┼────┘    │
                               └─────────┼─────────┼─────────┼─────────┘
                                         │         │         │
                                         ▼         ▼         ▼
                               ┌─────────────────────────────────────────┐
                               │           steve.py                      │
                               │                                         │
                               │  ┌──────────────────────────────────┐  │
                               │  │      STEVE AGENT                 │  │
                               │  │                                  │  │
                               │  │  - PersonaConfig                 │  │
                               │  │    • Name, Goals, Beliefs        │  │
                               │  │    • System Prompt               │  │
                               │  │    • Temperature, Model          │  │
                               │  │                                  │  │
                               │  │  - Context Management            │  │
                               │  │    • Message History             │  │
                               │  │    • Conversation State          │  │
                               │  │                                  │  │
                               │  │  - LLM Integration               │  │
                               │  │    • Ollama Client               │  │
                               │  │    • Request/Response            │  │
                               │  └────────┬────────────────┬────────┘  │
                               └───────────┼────────────────┼───────────┘
                                          │                │
                                          ▼                ▼
                         ┌────────────────────────┐  ┌─────────────────┐
                         │    memory.py           │  │  LLM (Ollama)   │
                         │                        │  │                 │
                         │ - MemoryStore          │  │ - llama3.1:8b   │
                         │ - SQLite Database      │  │ - qwen2.5       │
                         │ - Conversations        │  │ - mixtral       │
                         │ - Messages             │  │ - custom models │
                         │ - Agent State          │  └─────────────────┘
                         └────────────────────────┘
```

## Data Flow

### 1. Voice Input Flow
```
Microphone → AudioInput → VAD → Buffer → StreamingTranscriber 
    → WhisperSTT → Text → Orchestrator → Steve Agent → LLM 
    → Response → TTS → VoiceClone → Audio → Speaker
```

### 2. Text Input Flow
```
User Input → main.py → Orchestrator → VoiceCommandParser
    ├─ System Command → Orchestrator Actions
    └─ Chat Message → Active Steve → LLM → Response → Display
```

### 3. Multi-Agent Conversation Flow
```
User: "Let Steve and Alice talk"
    → Orchestrator.initiate_inter_agent_conversation()
    → Steve.process_input(topic, context={'inter_agent': True})
    → LLM generates Steve's response
    → Alice.process_input(steve_response, context={'inter_agent': True})
    → LLM generates Alice's response
    → Loop for N rounds
    → Save all messages to MemoryStore
```

## Component Interaction Matrix

```
┌──────────────┬────────┬─────┬─────┬────────┬───────┬──────────────┬──────┐
│              │ Audio  │ STT │ TTS │ Memory │ Steve │ Orchestrator │ Main │
├──────────────┼────────┼─────┼─────┼────────┼───────┼──────────────┼──────┤
│ Audio        │   -    │  ✓  │  -  │   -    │   -   │      ✓       │  ✓   │
│ STT          │   ✓    │  -  │  -  │   -    │   -   │      ✓       │  ✓   │
│ TTS          │   ✓    │  -  │  -  │   -    │   ✓   │      ✓       │  ✓   │
│ Memory       │   -    │  -  │  -  │   -    │   ✓   │      ✓       │  -   │
│ Steve        │   -    │  -  │  ✓  │   ✓    │   -   │      ✓       │  -   │
│ Orchestrator │   ✓    │  ✓  │  ✓  │   ✓    │   ✓   │      -       │  ✓   │
│ Main         │   ✓    │  ✓  │  ✓  │   ✓    │   ✓   │      ✓       │  -   │
└──────────────┴────────┴─────┴─────┴────────┴───────┴──────────────┴──────┘
```

## Configuration Hierarchy

```
config/settings.yaml
    ├── audio
    │   ├── input_device
    │   ├── output_device
    │   ├── sample_rate
    │   ├── channels
    │   ├── vad_enabled
    │   └── vad_threshold
    │
    ├── stt (Whisper)
    │   ├── model (tiny/base/small/medium/large)
    │   ├── language
    │   ├── device (cpu/cuda)
    │   └── compute_type
    │
    ├── llm (Ollama)
    │   ├── host
    │   ├── default_model
    │   ├── timeout
    │   └── context_window
    │
    ├── tts (Coqui)
    │   ├── model
    │   ├── language
    │   ├── device
    │   └── speed
    │
    ├── memory
    │   ├── db_path
    │   ├── max_context_messages
    │   └── chromadb settings
    │
    └── orchestrator
        ├── max_agents
        ├── default_persona
        └── inter_agent_enabled

personas/*.yaml
    ├── name
    ├── system_prompt
    ├── model
    ├── temperature
    ├── max_tokens
    ├── goals []
    ├── beliefs []
    ├── traits []
    ├── voice_sample
    └── voice_language
```

## Database Schema

```sql
-- Conversations Table
conversations
    ├── id (INTEGER PRIMARY KEY)
    ├── agent_name (TEXT)
    ├── started_at (TEXT)
    ├── ended_at (TEXT)
    ├── title (TEXT)
    └── created_at (TEXT)

-- Messages Table
messages
    ├── id (INTEGER PRIMARY KEY)
    ├── conversation_id (INTEGER FK)
    ├── role (TEXT: 'user'|'assistant'|'system')
    ├── content (TEXT)
    ├── agent_name (TEXT)
    ├── timestamp (TEXT)
    ├── metadata (TEXT JSON)
    └── created_at (TEXT)

-- Agent State Table
agent_state
    ├── agent_name (TEXT PRIMARY KEY)
    ├── state_data (TEXT JSON)
    └── updated_at (TEXT)
```

## State Management

### Agent State
```python
Steve {
    persona: PersonaConfig
    memory: MemoryStore
    llm: LLMClient
    voice: VoiceProfile
    conversation_id: int?
    context_messages: List[Message]
    is_active: bool
}
```

### Orchestrator State
```python
Orchestrator {
    agents: Dict[str, Steve]
    active_agent: Steve?
    audio_inputs: Dict[str, AudioInput]
    audio_outputs: Dict[str, AudioOutput]
    routes: List[AudioRoute]
    is_running: bool
}
```

## Execution Modes

### 1. Interactive Text Mode
```
main.py run --mode text
    → Initialize all components
    → Load personas
    → Start CLI input loop
    → Process each input through orchestrator
    → Display responses
```

### 2. Voice Mode
```
main.py run --mode voice
    → Initialize all components
    → Start audio input recording
    → Start streaming transcriber
    → Process transcriptions through orchestrator
    → Generate TTS responses
    → Play audio output
```

### 3. Programmatic Mode
```python
# See examples.py
memory = MemoryStore(...)
llm = LLMClient(...)
factory = SteveFactory(memory, llm)
steve = factory.create_from_config("persona.yaml")
steve.start_conversation()
response = steve.process_input("Hello")
```

## Extension Points

### Custom Audio Sources
```python
class CustomAudioInput(AudioInput):
    def _audio_callback(self, indata, frames, time, status):
        # Custom processing
        pass
```

### Custom LLM Backends
```python
class CustomLLMClient(LLMClient):
    def chat(self, model, messages, ...):
        # Integrate with other LLM APIs
        pass
```

### Custom Memory Stores
```python
class VectorMemoryStore(MemoryStore):
    def __init__(self, ...):
        # Use ChromaDB or similar
        pass
```

### Custom TTS Engines
```python
class CustomTTS(CoquiTTS):
    def synthesize(self, text, ...):
        # Use alternative TTS
        pass
```

## Performance Characteristics

### Latency Breakdown (Typical)
```
Voice Input → STT:           1-3 seconds (Whisper base)
STT → LLM:                   <0.1 seconds (routing)
LLM Processing:              0.5-5 seconds (depends on model size)
LLM → TTS:                   <0.1 seconds (routing)
TTS Generation:              2-5 seconds (Coqui XTTS)
TTS → Audio Output:          <0.5 seconds (playback)
────────────────────────────────────────────────────
Total End-to-End:           4-14 seconds
```

### Memory Usage (Approximate)
```
Base Application:            ~200MB
Whisper (base model):        ~150MB
TTS Model (XTTS v2):         ~1.5GB
LLM (llama3.1:8b):          ~5GB
Per Agent Context:           ~10MB
SQLite Database:             Minimal (<100MB typically)
────────────────────────────────────────────────────
Total Typical:              ~7GB
```

### Optimization Tips
1. Use smaller Whisper models (tiny/base) for faster STT
2. Use quantized LLMs (Q4/Q5) for lower memory
3. Reduce context window size
4. Enable VAD to reduce unnecessary processing
5. Use GPU acceleration if available
6. Batch TTS generation when possible

---

**This architecture enables:**
- ✅ 100% local, private AI interactions
- ✅ Multiple independent AI personas
- ✅ Voice cloning for each agent
- ✅ Persistent conversation memory
- ✅ Inter-agent communication
- ✅ Flexible audio routing
- ✅ Extensible plugin architecture
