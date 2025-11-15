#!/bin/bash
# bot-o'clock Quick Start Script
# Run this after installing dependencies

echo "🕒 bot-o'clock Quick Start"
echo "=========================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python $python_version"
echo ""

# Check if Ollama is running
echo "Checking Ollama..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✓ Ollama is running"
else
    echo "⚠ Ollama is not running"
    echo "  Start with: ollama serve"
    echo ""
fi

# Check for models
echo ""
echo "Available Ollama models:"
curl -s http://localhost:11434/api/tags 2>/dev/null | grep -o '"name":"[^"]*"' | cut -d'"' -f4 | head -5
echo ""

# Check if dependencies are installed
echo "Checking key dependencies..."
python3 -c "import sounddevice" 2>/dev/null && echo "✓ sounddevice" || echo "✗ sounddevice"
python3 -c "import yaml" 2>/dev/null && echo "✓ pyyaml" || echo "✗ pyyaml"
python3 -c "import rich" 2>/dev/null && echo "✓ rich" || echo "✗ rich"
python3 -c "import click" 2>/dev/null && echo "✓ click" || echo "✗ click"
echo ""

# List audio devices
echo "Audio devices:"
python3 src/main.py devices 2>/dev/null || echo "  Run 'python src/main.py devices' to list"
echo ""

# Show next steps
echo "=========================="
echo "Next Steps:"
echo "=========================="
echo ""
echo "1. Run installation test:"
echo "   python test_installation.py"
echo ""
echo "2. Start bot-o'clock (text mode):"
echo "   python src/main.py run --mode text"
echo ""
echo "3. Start bot-o'clock (voice mode):"
echo "   python src/main.py run --mode voice"
echo ""
echo "4. Try examples:"
echo "   python examples.py"
echo ""
echo "5. Create custom persona:"
echo "   python src/main.py create-persona 'MyAgent' --template creative"
echo ""
echo "=========================="
echo "For detailed help, see:"
echo "  - QUICKSTART.md  (fast start)"
echo "  - SETUP.md       (detailed setup)"
echo "  - INDEX.md       (complete reference)"
echo "=========================="
