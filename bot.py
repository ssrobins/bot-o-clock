#!/usr/bin/env python3
"""bot-o'clock Start Script
Simple launcher that passes commands to main.py
"""

import sys
import subprocess
import os


def main():
    """Main entry point"""
    main_script = os.path.join("src", "main.py")
    
    # Just pass all arguments through to main.py
    args = [sys.executable, main_script] + sys.argv[1:]
    
    try:
        subprocess.run(args)
    except KeyboardInterrupt:
        print("\n\nExiting...")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
