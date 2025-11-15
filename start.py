#!/usr/bin/env python3
"""bot-o'clock Quick Start Script
Run this after installing dependencies
"""

import sys
import subprocess
import urllib.request
import json


def check_python():
    """Check Python version"""
    version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    print(f"✓ Python {version}")


def check_ollama():
    """Check if Ollama is running"""
    try:
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2) as response:
            if response.status == 200:
                print("✓ Ollama is running")
                return True
    except Exception:
        pass
    
    print("⚠ Ollama is not running")
    print("  Start with: ollama serve")
    return False


def list_ollama_models():
    """List available Ollama models"""
    try:
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2) as response:
            data = json.loads(response.read())
            models = data.get("models", [])
            if models:
                print("\nAvailable Ollama models:")
                for model in models[:5]:
                    print(f"  - {model.get('name', 'unknown')}")
            else:
                print("\n⚠ No Ollama models found")
                print("  Pull a model with: ollama pull llama3.1:8b")
    except Exception:
        print("\nCouldn't fetch Ollama models")


def check_dependency(module_name, display_name=None):
    """Check if a Python module is installed"""
    if display_name is None:
        display_name = module_name
    
    try:
        __import__(module_name)
        print(f"✓ {display_name}")
        return True
    except ImportError:
        print(f"✗ {display_name}")
        return False


def check_dependencies():
    """Check key dependencies"""
    print("\nChecking key dependencies...")
    deps = [
        ("sounddevice", "sounddevice"),
        ("yaml", "pyyaml"),
        ("rich", "rich"),
        ("click", "click"),
    ]
    
    all_good = True
    for module, display in deps:
        if not check_dependency(module, display):
            all_good = False
    
    if not all_good:
        print("\n⚠ Missing dependencies. Install with:")
        print("  pip install -r requirements.txt")


def list_audio_devices():
    """List audio devices"""
    print("\nAudio devices:")
    try:
        result = subprocess.run(
            [sys.executable, "src/main.py", "devices"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(result.stdout)
        else:
            print("  Run 'python src/main.py devices' to list")
    except Exception:
        print("  Run 'python src/main.py devices' to list")


def show_next_steps():
    """Show next steps"""
    print("\n" + "=" * 50)
    print("Next Steps:")
    print("=" * 50)
    print("\n1. Run installation test:")
    print("   python test_installation.py")
    print("\n2. Start bot-o'clock (text mode):")
    print("   python src/main.py run --mode text")
    print("\n3. Start bot-o'clock (voice mode):")
    print("   python src/main.py run --mode voice")
    print("\n4. Try examples:")
    print("   python examples.py")
    print("\n5. Create custom persona:")
    print("   python src/main.py create-persona 'MyAgent' --template creative")
    print("\n" + "=" * 50)
    print("For detailed help, see:")
    print("  - QUICKSTART.md  (fast start)")
    print("  - SETUP.md       (detailed setup)")
    print("  - INDEX.md       (complete reference)")
    print("=" * 50)


def main():
    """Main entry point"""
    print("🕒 bot-o'clock Quick Start")
    print("=" * 50)
    print("\nChecking Python version...")
    check_python()
    
    print("\nChecking Ollama...")
    check_ollama()
    list_ollama_models()
    
    check_dependencies()
    list_audio_devices()
    show_next_steps()


if __name__ == "__main__":
    main()
