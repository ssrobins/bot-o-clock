#!/usr/bin/env python3
"""bot-o'clock Setup Script
Automated setup for the bot-o'clock project
"""

import os
import sys
import subprocess
import platform
import urllib.request
import shutil


def print_header(text):
    """Print a formatted header"""
    print(f"\n{'=' * 60}")
    print(f"  {text}")
    print(f"{'=' * 60}\n")


def print_step(step_num, text):
    """Print a step number"""
    print(f"\n[{step_num}] {text}")
    print("-" * 60)


def run_command(cmd, check=True, shell=False, cwd=None):
    """Run a shell command and return success status"""
    try:
        if shell:
            result = subprocess.run(cmd, shell=True, check=check, capture_output=True, text=True, cwd=cwd)
        else:
            result = subprocess.run(cmd, check=check, capture_output=True, text=True, cwd=cwd)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr
    except FileNotFoundError:
        return False, "Command not found"


def find_compatible_python():
    """Find a compatible Python version (3.10 only)"""
    print_step(1, "Finding Compatible Python Version")

    # Try different Python commands for 3.10
    python_commands = [
        "python3.10",
        "python3",
        "python"
    ]

    for cmd in python_commands:
        if shutil.which(cmd):
            # Check version
            try:
                result = subprocess.run(
                    [cmd, "-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                version = result.stdout.strip()
                major, minor = map(int, version.split('.'))

                if major == 3 and minor == 10:
                    print(f"✓ Found compatible Python: {cmd} (version {version})")
                    return cmd, version
            except Exception:
                continue

    print("✗ No compatible Python version found")
    print("\nPython 3.10 is required (TTS library requires <3.11)")
    print("\nTo install Python 3.10:")
    print("  brew install python@3.10")
    return None, None


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


def create_virtual_environment(python_cmd):
    """Create a virtual environment with the compatible Python version"""
    print_step(3, "Creating Virtual Environment")

    venv_path = "venv"

    # Check if venv already exists (shouldn't happen if cleanup was done, but just in case)
    if os.path.exists(venv_path):
        print(f"Using existing virtual environment at '{venv_path}'")
        return True, venv_path

    print(f"Creating virtual environment with {python_cmd}...")
    success, output = run_command([python_cmd, "-m", "venv", venv_path])

    if success:
        print(f"✓ Virtual environment created at '{venv_path}'")
        return True, venv_path
    else:
        print(f"✗ Failed to create virtual environment")
        print(output)
        return False, None


def install_system_dependencies():
    """Install system dependencies via Homebrew"""
    if platform.system() != "Darwin":
        print_step(4, "Skipping system dependencies (non-macOS)")
        print("Please install portaudio and ffmpeg manually for your system")
        return True

    print_step(4, "Installing System Dependencies")

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

    # Skip BlackHole - requires reboot and most users don't need it
    print("\n" + "=" * 60)
    print("Note: BlackHole (optional virtual audio driver) NOT installed")
    print("=" * 60)
    print("BlackHole is for advanced audio routing between applications.")
    print("It requires a system reboot and most users don't need it.")
    print("")
    print("If you want to install it later:")
    print("  brew install blackhole-2ch")
    print("  (then reboot your system)")
    print("=" * 60)

    return all_success


def install_python_dependencies(venv_path):
    """Install Python dependencies from requirements.txt"""
    print_step(5, "Installing Python Dependencies")

    if not os.path.exists("requirements.txt"):
        print("✗ requirements.txt not found")
        return False

    # Get the path to the venv pip
    if platform.system() == "Windows":
        pip_path = os.path.join(venv_path, "Scripts", "pip")
    else:
        pip_path = os.path.join(venv_path, "bin", "pip")

    print("Upgrading pip...")
    run_command([pip_path, "install", "--upgrade", "pip"], check=False)

    print("\nInstalling dependencies (this may take several minutes)...")
    success, output = run_command([pip_path, "install", "-r", "requirements.txt"])

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
    print_step(6, "Installing Ollama")

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
    print_step(7, "Starting Ollama Service")

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
            print("Waiting for Ollama to start...")
            
            # Wait up to 10 seconds for Ollama to start
            for i in range(10):
                time.sleep(1)
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
    print_step(8, "Pulling Ollama Models")

    if not check_ollama_running():
        print("⚠ Ollama is not running. Start it with: ollama serve")
        return False

    print("\n" + "=" * 60)
    print("LLM Model Required")
    print("=" * 60)
    print("bot-o'clock requires a language model to function.")
    print("Models power the AI agents' reasoning and responses.")
    print("")
    print("llama3.1:8b:")
    print("  - Size: ~4.7 GB")
    print("  - Good balance of speed and quality")
    print("  - Works well on most modern Macs")
    print("")
    print("You can install additional models later with:")
    print("  ollama pull <model-name>")
    print("  ollama list  (to see installed models)")
    print("=" * 60)

    print("\nPull llama3.1:8b (required)?")
    response = input("(y/n): ").lower().strip()

    if response == 'y':
        print("\nPulling llama3.1:8b (this may take several minutes)...")
        success, _ = run_command(["ollama", "pull", "llama3.1:8b"])
        if success:
            print("✓ Model pulled successfully")
            return True
        else:
            print("✗ Failed to pull model")
            return False
    else:
        print("\n⚠ Skipping model pull. You'll need to pull a model manually later:")
        print("  ollama pull llama3.1:8b")
        return False


def run_tests(venv_path):
    """Run installation tests"""
    print_step(9, "Running Installation Tests")

    if not os.path.exists("test_installation.py"):
        print("⚠ test_installation.py not found, skipping tests")
        return True

    response = input("Run installation tests? (y/n): ").lower().strip()
    if response != 'y':
        print("Skipping tests")
        return True

    # Get the path to the venv python
    if platform.system() == "Windows":
        python_path = os.path.join(venv_path, "Scripts", "python")
    else:
        python_path = os.path.join(venv_path, "bin", "python")

    print("\nRunning tests...\n")
    
    # Run tests and capture output
    try:
        result = subprocess.run(
            [python_path, "test_installation.py"],
            capture_output=True,
            text=True
        )
        
        # Print both stdout and stderr
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        
        if result.returncode == 0:
            print("\n✓ All tests passed")
            return True
        else:
            print("\n✗ Some tests failed")
            print("\nTo fix issues:")
            print("  1. Check the test output above for specific failures")
            print("  2. See SETUP.md for troubleshooting")
            print("  3. Ensure Ollama is running: ollama serve")
            print("  4. Ensure model is pulled: ollama pull llama3.1:8b")
            return False
    except Exception as e:
        print(f"\n✗ Failed to run tests: {e}")
        return False


def show_next_steps(venv_path):
    """Show next steps after setup"""
    print_header("Setup Complete!")

    # Activation command
    if platform.system() == "Windows":
        activate_cmd = f"{venv_path}\\Scripts\\activate"
    else:
        activate_cmd = f"source {venv_path}/bin/activate"

    print("IMPORTANT: Activate the virtual environment first:")
    print(f"   {activate_cmd}")
    print("\nThen you can:")
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


def clean_venv():
    """Clean up virtual environment"""
    print_header("🧹 Clean Virtual Environment")

    if os.path.exists("venv"):
        print("Removing virtual environment...")
        shutil.rmtree("venv")
        print("✓ Virtual environment removed")
    else:
        print("No virtual environment found")

    print("\nTo set up again, run:")
    print("  python3 setup.py")


def main():
    """Main setup routine"""
    # Check for clean argument
    if len(sys.argv) > 1 and sys.argv[1] == "clean":
        clean_venv()
        return

    print_header("🕒 bot-o'clock Setup")

    # Check if running on macOS
    if platform.system() != "Darwin":
        print("⚠️  This automated setup script is designed for macOS only.\n")
        print(f"Detected platform: {platform.system()}")
        print("\nFor Linux/Windows installation:")
        print("  Please follow the manual setup instructions in SETUP.md")
        print("  See: https://github.com/ssrobins/bot-o-clock/blob/main/SETUP.md")
        print("\nThe manual setup includes platform-specific instructions for:")
        print("  - Installing system dependencies (portaudio, ffmpeg)")
        print("  - Setting up Python virtual environment")
        print("  - Installing Ollama")
        print("  - Installing Python packages")
        sys.exit(0)

    # Check for existing venv and offer to clean up
    if os.path.exists("venv"):
        print("⚠️  Found existing virtual environment")
        response = input("Remove it and start fresh? (y/N): ").lower().strip()
        if response == 'y':
            print("Removing existing virtual environment...")
            shutil.rmtree("venv")
            print("✓ Cleaned up\n")
        else:
            print("Keeping existing venv (setup will try to use it)\n")

    print("This script will guide you through setting up bot-o'clock.\n")
    print("Steps:")
    print("  1. Find compatible Python (3.10 only)")
    print("  2. Check Homebrew (macOS)")
    print("  3. Create virtual environment")
    print("  4. Install system dependencies")
    print("  5. Install Python dependencies")
    print("  6. Install Ollama")
    print("  7. Start Ollama service")
    print("  8. Pull LLM models")
    print("  9. Run tests")

    response = input("\nContinue? (y/n): ").lower().strip()
    if response != 'y':
        print("Setup cancelled.")
        return

    # Step 1: Find compatible Python
    python_cmd, python_version = find_compatible_python()
    if not python_cmd:
        print("\n⚠ Setup incomplete. Please install a compatible Python version.")
        sys.exit(1)

    # Step 2: Check Homebrew
    if not check_homebrew():
        print("\n⚠ Setup incomplete. Please install Homebrew first.")
        sys.exit(1)

    # Step 3: Create virtual environment
    success, venv_path = create_virtual_environment(python_cmd)
    if not success:
        print("\n⚠ Setup incomplete. Failed to create virtual environment.")
        sys.exit(1)

    # Step 4: Install system dependencies
    if not install_system_dependencies():
        print("\n⚠ Setup incomplete. Failed to install system dependencies.")
        sys.exit(1)

    # Step 5: Install Python dependencies
    if not install_python_dependencies(venv_path):
        print("\n⚠ Setup incomplete. Failed to install Python dependencies.")
        sys.exit(1)

    # Step 6: Install Ollama
    if not install_ollama():
        print("\n⚠ Setup incomplete. Failed to install Ollama.")
        sys.exit(1)

    # Step 7: Start Ollama
    ollama_started = start_ollama()
    if not ollama_started:
        print("\n⚠ Ollama not running. You'll need to start it manually.")

    # Step 8: Pull models
    models_pulled = pull_ollama_models()
    if not models_pulled:
        print("\n⚠ Failed to pull models. You can pull them later with: ollama pull llama3.1:8b")

    # Step 9: Run tests
    tests_passed = run_tests(venv_path)

    # Check overall success
    setup_success = ollama_started and models_pulled and tests_passed

    if setup_success:
        show_next_steps(venv_path)
    else:
        print("\n" + "=" * 60)
        print("⚠ Setup completed with warnings")
        print("=" * 60)
        if not ollama_started:
            print("  - Ollama not started automatically")
        if not models_pulled:
            print("  - Model not pulled")
        if not tests_passed:
            print("  - Some tests failed")
        print("\nReview the output above and see SETUP.md for help.")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
