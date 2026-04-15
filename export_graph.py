# ============================================================
# export_graph.py
# Exports the agent graph as a PNG image.
# LangGraph can render the graph using the Mermaid.ink API
# (requires internet connection — calls mermaid.ink online).
#
# Output: storage/graph_visualization.png
# Usage:  python export_graph.py
# ============================================================

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from agents.sales_quote.graph import build_sales_quote_graph

OUTPUT_PATH = "storage/graph_visualization.png"

print("Building graph...")
app = build_sales_quote_graph()

print("Rendering graph to PNG (calling mermaid.ink API)...")
png_bytes = app.get_graph().draw_mermaid_png()

with open(OUTPUT_PATH, "wb") as f:
    f.write(png_bytes)

print(f"Graph saved to: {OUTPUT_PATH}")
print(f"File size: {len(png_bytes):,} bytes")
