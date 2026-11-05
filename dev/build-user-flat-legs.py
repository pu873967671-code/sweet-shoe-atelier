#!/usr/bin/env python3
"""Rebuild flat from its independent immutable-source seating calibration."""
from pathlib import Path
import runpy

def build():
    module = runpy.run_path(str(Path(__file__).with_name('build-calibrated-user-legs.py')))
    module['build']('flat')

if __name__ == '__main__':
    build()
