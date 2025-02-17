"""Main entry point for the application."""
import os
import sys

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from expert.ui import run

if __name__ == "__main__":
    run() 