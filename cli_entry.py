#!/usr/bin/env python3
"""CLI entry point for multi-turn conversation"""

import os
import sys
from pathlib import Path

# Get project root
PROJECT_ROOT = Path(__file__).parent.absolute()

# Add to path
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Change to project directory
os.chdir(PROJECT_ROOT)

# Load environment
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

# Run CLI
from src.cli.cli_app import main

if __name__ == "__main__":
    main()
