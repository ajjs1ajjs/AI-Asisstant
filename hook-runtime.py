"""Runtime hook: ensure local project modules are importable."""
import sys
import os

# Add _MEIPASS (PyInstaller's temp extraction dir) to sys.path
# so that local modules like agent_tools.py, orchestrator.py etc. are found
if getattr(sys, 'frozen', False):
    base = sys._MEIPASS
    if base not in sys.path:
        sys.path.insert(0, base)
