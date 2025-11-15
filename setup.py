#!/usr/bin/env python3
"""bot-o'clock Setup Script
Automated setup for the bot-o'clock project
"""

import os
import sys
import subprocess
import platform
import urllib.request


def print_header(text):
    """Print a formatted header"""
    print(f"\n{'=' * 60}")
    print(f"  {text}")
    print(f"{'=' * 60}\n")


def print_step(step_num, text):
    """Print a step number"""
    print(f"\n[{step_num}] {text}")
    print("-" * 60)


def run_command(cmd, check=True, shell=False):
    """Run a shell command and return success status"""
    try:
        if shell:
            result = subprocess.run(cmd, shell=True, check=check, capture_output=True, text=True)
        else:
            result = subprocess.run(cmd, check=check, capture_output=True, text=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr
    except FileNotFoundError:
        return False, "Command not found"


def check_python_version():
    """Check if Python version is 3.10+"""
    print_step(1, "Checking Python Version")
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    
    if version.major >= 3 and version.minor >= 10:
        print(f"✓ Python {version_str} - OK")
        return True
    else:
        print(f"✗ Python {version_str} - Need Python 3.10+")
        print("\nPlease upgrade Python:")
        print("  brew install python@3.11")
        return False


def check_homebrew():
    """Check if Homebrew is installed (macOS)"""
    if platform.system() != "Darwin":
        return True  # Skip on non-macOS
    
    print_step(2, "Checking Homebrew")
    success, _ = run_command(["brew", "--version"])
    
    if success:
        print("✓ Homebrew is installed")
        return True
    else:
        print("✗ Homebrew not found")
        print("\nInstall Homebrew:")
        print('  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"')
        return False


def install_system_dependencies():
    """Install system dependencies via Homebrew"""
    if platform.system() != "Darwin":
        print_step(3, "Skipping system dependencies (non-macOS)")
        print("Please install portaudio and ffmpeg manually for your system")
        return True
    
    print_step(3, "Installing System Dependencies")
    
    packages = ["portaudio", "ffmpeg"]
    all_success = True
    
    for package in packages:
        print(f"\nInstalling {package}...")
        success, output = run_command(["brew", "install", package])
        if success or "already installed" in output.lower():
            print(f"✓ {package}")
        else:
            print(f"✗ Failed to install {package}")
            all_success = False
    
    # Optional: BlackHole
    print("\nOptional: BlackHole for virtual audio routing")
    response = input("Install BlackHole? (y/n): ").lower().strip()
    if response == 'y':
        success, _ = run_command(["brew", "install", "blackhole-2ch"])
        if success:
            print("✓ BlackHole installed")
        else:
            print("⚠ BlackHole installation failed (optional)")
    
    return all_success


def install_python_dependencies():
    """Install Python dependencies from requirements.txt"""
    print_step(4, "Installing Python Dependencies")
    
    if not os.path.exists("requirements.txt"):
        print("✗ requirements.txt not found")
        return False
    
    print("Upgrading pip...")
    run_command([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], check=False)
    
    print("\nInstalling dependencies (this may take several minutes)...")
    success, output = run_command([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    
    if success:
        print("✓ Python dependencies installed")
        return True
    else:
        print("✗ Failed to install dependencies")
        print(output)
        return False


def check_ollama_installed():
    """Check if Ollama is installed"""
    success, _ = run_command(["ollama", "--version"])
    return success


def install_ollama():
    """Install Ollama"""
    print_step(5, "Installing Ollama")
    
    if check_ollama_installed():
        print("✓ Ollama already installed")
        return True
    
    if platform.system() == "Darwin":
        print("Installing Ollama via Homebrew...")
        success, _ = run_command(["brew", "install", "ollama"])
        if success:
            print("✓ Ollama installed")
            return True
        else:
            print("✗ Failed to install Ollama via Homebrew")
            print("\nManual installation:")
            print("  Visit: https://ollama.ai/download")
            return False
    else:
        print("Please install Ollama manually:")
        print("  Visit: https://ollama.ai/download")
        return False


def check_ollama_running():
    """Check if Ollama service is running"""
    try:
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2) as response:
            return response.status == 200
    except Exception:
        return False


def start_ollama():
    """Start Ollama service"""
    print_step(6, "Starting Ollama Service")
    
    if check_ollama_running():
        print("✓ Ollama is already running")
        return True
    
    print("Starting Ollama in the background...")
    print("(You may need to start it manually in another terminal with: ollama serve)")
    
    # Try to start Ollama in background
    try:
        if platform.system() == "Darwin":
            # On macOS, try to start as a background service
            subprocess.Popen(["ollama", "serve"], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
            import time
            time.sleep(2)  # Give it time to start
            
            if check_ollama_running():
                print("✓ Ollama started")
                return True
    except Exception:
        pass
    
    print("⚠ Could not automatically start Ollama")
    print("Please run in another terminal: ollama serve")
    return False


def pull_ollama_models():
    """Pull recommended Ollama models"""
    print_step(7, "Pulling Ollama Models")
    
    if not check_ollama_running():
        print("⚠ Ollama is not running. Start it with: ollama serve")
        return False
    
    print("\nRecommended model: llama3.1:8b")
    response = input("Pull llama3.1:8b? (y/n): ").lower().strip()
    
    if response == 'y':
        print("\nPulling llama3.1:8b (this may take several minutes)...")
        success, _ = run_command(["ollama", "pull", "llama3.1:8b"])
        if success:
            print("✓ Model pulled successfully")
        else:
            print("✗ Failed to pull model")
            return False
    
    print("\nOptional: llama3.1:70b (requires significant resources)")
    response = input("Pull llama3.1:70b? (y/n): ").lower().strip()
    
    if response == 'y':
        print("\nPulling llama3.1:70b (this will take a while)...")
        success, _ = run_command(["ollama", "pull", "llama3.1:70b"])
        if success:
            print("✓ Model pulled successfully")
        else:
            print("⚠ Failed to pull model (optional)")
    
    return True


def run_tests():
    """Run installation tests"""
    print_step(8, "Running Installation Tests")
    
    if not os.path.exists("test_installation.py"):
        print("⚠ test_installation.py not found, skipping tests")
        return True
    
    response = input("Run installation tests? (y/n): ").lower().strip()
    if response != 'y':
        print("Skipping tests")
        return True
    
    print("\nRunning tests...")
    success, output = run_command([sys.executable, "test_installation.py"])
    
    if success:
        print("✓ Tests passed")
        print(output)
        return True
    else:
        print("⚠ Some tests failed")
        print(output)
        return False


def show_next_steps():
    """Show next steps after setup"""
    print_header("Setup Complete!")
    
    print("Next Steps:")
    print("\n1. Verify setup:")
    print("   python start.py")
    print("\n2. Start bot-o'clock (text mode):")
    print("   python src/main.py run --mode text")
    print("\n3. Start with voice:")
    print("   python src/main.py run --mode voice")
    print("\n4. Create a custom persona:")
    print("   python src/main.py create-persona 'MyAgent' --template creative")
    print("\n5. Read the documentation:")
    print("   - QUICKSTART.md  (fast start)")
    print("   - SETUP.md       (detailed info)")
    print("   - README.md      (full guide)")
    
    print("\n" + "=" * 60)


def main():
    """Main setup routine"""
    print_header("🕒 bot-o'clock Setup")
    
    print("This script will guide you through setting up bot-o'clock.\n")
    print("Steps:")
    print("  1. Check Python version")
    print("  2. Check Homebrew (macOS)")
    print("  3. Install system dependencies")
    print("  4. Install Python dependencies")
    print("  5. Install Ollama")
    print("  6. Start Ollama service")
    print("  7. Pull LLM models")
    print("  8. Run tests")
    
    response = input("\nContinue? (y/n): ").lower().strip()
    if response != 'y':
        print("Setup cancelled.")
        return
    
    # Run setup steps
    steps = [
        check_python_version,
        check_homebrew,
        install_system_dependencies,
        install_python_dependencies,
        install_ollama,
        start_ollama,
        pull_ollama_models,
        run_tests,
    ]
    
    for step in steps:
        if not step():
            print(f"\n⚠ Setup incomplete. Please resolve the issue above and run setup.py again.")
            sys.exit(1)
    
    show_next_steps()


if __name__ == "__main__":
    main()
