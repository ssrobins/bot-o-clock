#!/usr/bin/env python3
"""
Test script for bot-o'clock components
Run this to verify your installation
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def print_header(text):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")


def test_imports():
    """Test if all modules can be imported"""
    print_header("Testing Module Imports")
    
    modules = [
        'audio_input',
        'stt',
        'tts',
        'memory',
        'steve',
        'orchestrator',
        'main'
    ]
    
    success = 0
    failed = []
    
    for module in modules:
        try:
            __import__(module)
            print(f"✓ {module}")
            success += 1
        except Exception as e:
            print(f"✗ {module}: {e}")
            failed.append(module)
    
    print(f"\n{success}/{len(modules)} modules imported successfully")
    if failed:
        print(f"Failed: {', '.join(failed)}")
    
    return len(failed) == 0


def test_ollama():
    """Test Ollama connection"""
    print_header("Testing Ollama Connection")
    
    try:
        from steve import LLMClient
        llm = LLMClient()
        
        if llm.check_connection():
            print("✓ Ollama is running and accessible")
            
            # Try to get available models
            import requests
            response = requests.get(f"{llm.host}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                if models:
                    print(f"✓ Available models: {len(models)}")
                    for model in models[:5]:  # Show first 5
                        print(f"  - {model['name']}")
                else:
                    print("⚠ No models found. Run: ollama pull llama3.1:8b")
            return True
        else:
            print("✗ Ollama not running")
            print("  Start with: ollama serve")
            return False
    except Exception as e:
        print(f"✗ Error checking Ollama: {e}")
        return False


def test_audio():
    """Test audio devices"""
    print_header("Testing Audio Devices")
    
    try:
        from audio_input import AudioInput
        from tts import AudioOutput
        
        # Input devices
        input_devices = AudioInput.list_devices()
        print(f"✓ Found {len(input_devices)} input device(s)")
        for idx, info in list(input_devices.items())[:3]:
            print(f"  [{idx}] {info['name']}")
        
        # Output devices
        output_devices = AudioOutput.list_output_devices()
        print(f"✓ Found {len(output_devices)} output device(s)")
        for idx, info in list(output_devices.items())[:3]:
            print(f"  [{idx}] {info['name']}")
        
        return True
    except Exception as e:
        print(f"✗ Error testing audio: {e}")
        return False


def test_whisper():
    """Test Whisper model"""
    print_header("Testing Whisper (STT)")
    
    try:
        from stt import STTConfig, create_stt
        
        print("Loading Whisper model (this may take a moment)...")
        config = STTConfig(model_size="tiny")  # Use tiny for quick test
        stt = create_stt(config)
        
        print(f"✓ Whisper model loaded: {config.model_size}")
        print(f"  Device: {config.device}")
        return True
    except Exception as e:
        print(f"✗ Error loading Whisper: {e}")
        print("  This is normal if faster-whisper or openai-whisper aren't installed")
        return False


def test_memory():
    """Test memory store"""
    print_header("Testing Memory Store")
    
    try:
        from memory import MemoryStore, Message
        from datetime import datetime
        import os
        
        # Create test database
        db_path = "data/test_setup.db"
        os.makedirs("data", exist_ok=True)
        
        store = MemoryStore(db_path)
        
        # Create test conversation
        conv_id = store.create_conversation("TestAgent", "Test")
        print(f"✓ Created conversation: {conv_id}")
        
        # Add test message
        msg = Message(
            role="user",
            content="Test message",
            timestamp=datetime.utcnow().isoformat(),
            agent_name="TestAgent"
        )
        store.add_message(conv_id, msg)
        print("✓ Added message to conversation")
        
        # Retrieve messages
        messages = store.get_messages(conv_id)
        print(f"✓ Retrieved {len(messages)} message(s)")
        
        # Cleanup
        import os
        if os.path.exists(db_path):
            os.remove(db_path)
        
        return True
    except Exception as e:
        print(f"✗ Error testing memory: {e}")
        return False


def test_personas():
    """Test persona loading"""
    print_header("Testing Persona Files")
    
    try:
        from steve import PersonaConfig
        import glob
        
        persona_files = glob.glob("personas/*.yaml")
        
        if not persona_files:
            print("⚠ No persona files found in personas/")
            return False
        
        print(f"Found {len(persona_files)} persona file(s):")
        
        for file in persona_files:
            try:
                persona = PersonaConfig.from_yaml(file)
                print(f"✓ {persona.name} ({os.path.basename(file)})")
            except Exception as e:
                print(f"✗ {os.path.basename(file)}: {e}")
        
        return True
    except Exception as e:
        print(f"✗ Error testing personas: {e}")
        return False


def test_config():
    """Test configuration file"""
    print_header("Testing Configuration")
    
    try:
        import yaml
        
        config_path = "config/settings.yaml"
        if not os.path.exists(config_path):
            print(f"✗ Config file not found: {config_path}")
            return False
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        print("✓ Configuration loaded")
        
        # Check key sections
        sections = ['audio', 'stt', 'llm', 'tts', 'memory', 'orchestrator']
        for section in sections:
            if section in config:
                print(f"  ✓ {section} section found")
            else:
                print(f"  ⚠ {section} section missing")
        
        return True
    except Exception as e:
        print(f"✗ Error testing config: {e}")
        return False


def main():
    """Run all tests"""
    print("="*60)
    print("  bot-o'clock Installation Test")
    print("="*60)
    
    results = {
        "Module Imports": test_imports(),
        "Configuration": test_config(),
        "Persona Files": test_personas(),
        "Memory Store": test_memory(),
        "Audio Devices": test_audio(),
        "Ollama Connection": test_ollama(),
        "Whisper STT": test_whisper(),
    }
    
    print_header("Test Summary")
    
    passed = sum(results.values())
    total = len(results)
    
    for test, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! bot-o'clock is ready to use!")
        print("\nQuick start:")
        print("  python src/main.py run --mode text")
    else:
        print("\n⚠ Some tests failed. Check the output above.")
        print("See SETUP.md for detailed installation instructions.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
