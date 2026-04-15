# ============================================================
# main.py
# Entry point — launches the Gradio web UI.
# Usage: python main.py
# ============================================================

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from ui.app import demo

if __name__ == "__main__":
    demo.launch()
