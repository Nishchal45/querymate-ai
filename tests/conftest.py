"""Shared pytest fixtures."""

import os
import sys
from pathlib import Path

# Ensure backend imports work without installing the package
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Set safe defaults for tests
os.environ.setdefault('OPENAI_API_KEY', 'sk-test-fake')
os.environ.setdefault('APP_ENV', 'test')
