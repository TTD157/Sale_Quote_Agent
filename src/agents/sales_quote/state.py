# ============================================================
# src/agents/sales_quote/state.py
# Defines the shared data object that flows through all nodes.
# Every node can read and update these fields.
# ============================================================

from typing import TypedDict


class SalesQuoteState(TypedDict):
    # ── INPUT ────────────────────────────────────────────────
    raw_input:           str   # original unstructured text from the salesperson

    # ── NODE 1 OUTPUT — Requirements extraction ──────────────
    requirements:        dict  # structured client needs (role, tech, budget, timeline...)

    # ── NODE 2 OUTPUT — Delivery capacity check ──────────────
    available_resources: dict  # matched employees + gaps
    capacity_context:    str   # raw text retrieved from the roster RAG

    # ── NODE 3 OUTPUT — Package configuration ────────────────
    package_config:      dict  # proposed team (specific people + roles)

    # ── NODE 4 OUTPUT — Pricing & policy validation ──────────
    pricing_result:      dict  # pricing breakdown table
    policy_valid:        bool  # True if margin >= minimum
    retry_count:         int   # number of retry attempts so far (max 2)
    retry_feedback:      str   # what Node 3 must fix on the next retry

    # ── NODE 5 OUTPUT — Final output ─────────────────────────
    final_output:        str   # formatted summary ready for the sales team
