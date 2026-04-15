# ============================================================
# src/agents/sales_quote/graph.py
# Assembles and compiles the full LangGraph workflow.
#
# Graph structure:
#   START
#     -> extract_requirements_node
#     -> check_capacity_node
#     -> configure_package_node
#     -> pricing_and_policy_node
#          -> (pass)    -> generate_output_node -> END
#          -> (fail)    -> configure_package_node (retry loop)
#          -> (max retry) -> generate_output_node -> END
# ============================================================

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from agents.sales_quote.state import SalesQuoteState
from agents.sales_quote.nodes import (
    extract_requirements_node,
    check_capacity_node,
    configure_package_node,
    pricing_and_policy_node,
    generate_output_node,
    route_after_pricing,
)


def build_sales_quote_graph():
    """
    Assembles and compiles the sales quote agent graph.
    Returns a compiled app ready to invoke.
    """
    graph = StateGraph(SalesQuoteState)

    # ── ADD NODES ────────────────────────────────────────────
    graph.add_node("extract_requirements_node", extract_requirements_node)
    graph.add_node("check_capacity_node",       check_capacity_node)
    graph.add_node("configure_package_node",    configure_package_node)
    graph.add_node("pricing_and_policy_node",   pricing_and_policy_node)
    graph.add_node("generate_output_node",      generate_output_node)

    # ── SET ENTRY POINT ──────────────────────────────────────
    graph.set_entry_point("extract_requirements_node")

    # ── ADD EDGES ────────────────────────────────────────────
    # Forward path: extract -> capacity -> configure -> pricing
    graph.add_edge("extract_requirements_node", "check_capacity_node")
    graph.add_edge("check_capacity_node",       "configure_package_node")
    graph.add_edge("configure_package_node",    "pricing_and_policy_node")

    # Conditional edge from pricing:
    # Either move forward to output, or loop back to configure (retry)
    graph.add_conditional_edges(
        "pricing_and_policy_node",
        route_after_pricing,
        {
            "configure_package_node": "configure_package_node",  # loop back
            "generate_output_node":   "generate_output_node"     # move forward
        }
    )

    # Final edge
    graph.add_edge("generate_output_node", END)

    # ── COMPILE ──────────────────────────────────────────────
    # MemorySaver keeps state in memory during a session
    return graph.compile(checkpointer=MemorySaver())
