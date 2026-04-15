# ============================================================
# src/agents/sales_quote/nodes.py
# Each function here is one node in the LangGraph workflow.
#
# Flow: extract -> capacity -> configure -> pricing -> output
#                                 ^              |
#                                 |__ retry _____|
# ============================================================

import json
import datetime
from langchain_core.messages import SystemMessage, HumanMessage
from core.llm import get_llm
from rag.retriever import create_delivery_retriever_tool, create_pricing_retriever_tool
from agents.sales_quote.state import SalesQuoteState
from agents.sales_quote.prompts import (
    EXTRACT_REQUIREMENTS_PROMPT,
    CAPACITY_CHECK_PROMPT,
    CONFIGURE_PACKAGE_PROMPT,
    PRICING_PROMPT,
    OUTPUT_PROMPT,
)


# ── DATE CONTEXT ─────────────────────────────────────────────
def date_context() -> str:
    """
    Returns a short block telling the LLM what today's date is.
    Injected into every node that does temporal reasoning so
    'tomorrow', 'next week', 'ASAP' all resolve to real dates.
    """
    today    = datetime.date.today()
    tomorrow = today + datetime.timedelta(days=1)
    next_wk  = today + datetime.timedelta(days=7)
    next_mo  = (today.replace(day=1) + datetime.timedelta(days=32)).replace(day=1)
    return (
        f"=== DATE CONTEXT (use this to resolve all relative dates) ===\n"
        f"Today         : {today.isoformat()}\n"
        f"Tomorrow      : {tomorrow.isoformat()}\n"
        f"Next week     : {next_wk.isoformat()}\n"
        f"Next month    : {next_mo.isoformat()}\n"
        f"=============================================================\n"
    )


# ── HELPER ───────────────────────────────────────────────────
def parse_llm_json(response) -> dict | list:
    """
    Extract text from Gemini response and parse it as JSON.
    Handles both list-of-blocks format and plain string format.
    Also strips markdown code fences like ```json ... ```.
    """
    # Gemini sometimes returns content as a list of typed blocks
    if isinstance(response.content, list):
        raw = response.content[0].get("text", "") if response.content else ""
    else:
        raw = response.content

    # Remove markdown code fences if the LLM wrapped its JSON in them
    raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    return json.loads(raw)


# ============================================================
# NODE 1 — EXTRACT REQUIREMENTS
# Input:  raw_input (messy unstructured text)
# Output: requirements (structured JSON dict)
# ============================================================

def extract_requirements_node(state: SalesQuoteState) -> dict:
    print("\n--- Node 1: extract_requirements_node ---")
    llm = get_llm()

    response = llm.invoke([
        SystemMessage(content=EXTRACT_REQUIREMENTS_PROMPT),
        HumanMessage(content=f"{date_context()}\nSALES NOTES:\n{state['raw_input']}")
    ])

    try:
        requirements = parse_llm_json(response)
        print(f"    Extracted: {len(requirements.get('roles_needed', []))} role(s) needed")
        print(f"    Client: {requirements.get('client_name', 'unknown')}")
        print(f"    Domain: {requirements.get('project_domain', 'unknown')}")
    except Exception as e:
        print(f"    JSON parse failed ({e}) — using empty requirements")
        requirements = {"roles_needed": [], "budget_usd": None, "duration_months": None}

    return {"requirements": requirements}


# ============================================================
# NODE 2 — CHECK DELIVERY CAPACITY
# Input:  requirements (dict)
# Output: available_resources (dict), capacity_context (str)
#
# How it works:
# 1. Build a search query from each required role + tech stack
# 2. Search the delivery roster RAG to get matching employee records
# 3. Ask the LLM to analyze who matches each requirement
# ============================================================

def check_capacity_node(state: SalesQuoteState) -> dict:
    print("\n--- Node 2: check_capacity_node ---")

    requirements = state["requirements"]
    search_tool = create_delivery_retriever_tool()

    # Build search queries from each required role
    # e.g., "Senior Backend Developer Node.js TypeScript"
    roles_needed = requirements.get("roles_needed", [])
    tech_stack = requirements.get("tech_stack", [])

    all_context_parts = []

    for role_req in roles_needed:
        role = role_req.get("role", "Developer")
        seniority = role_req.get("seniority", "")
        parts = [p for p in [seniority, role] + tech_stack[:3] if p and str(p).lower() != "null" and str(p).lower() != "none"]
        query = " ".join(parts)

        print(f"    Searching roster for: '{query}'")
        result = search_tool.invoke(query)
        all_context_parts.append(f"[Search for: {query}]\n{result}")

    # If no roles specified, do a general search
    if not all_context_parts:
        result = search_tool.invoke("available developer")
        all_context_parts.append(result)

    capacity_context = "\n\n---\n\n".join(all_context_parts)

    # Ask LLM to analyze the retrieved roster data and identify matches
    llm = get_llm()
    response = llm.invoke([
        SystemMessage(content=CAPACITY_CHECK_PROMPT),
        HumanMessage(content=f"""
{date_context()}
CLIENT REQUIREMENTS:
{json.dumps(requirements, indent=2, ensure_ascii=False)}

ROSTER DATA (retrieved from database):
{capacity_context}
""")
    ])

    try:
        available_resources = parse_llm_json(response)
        matches = available_resources.get("matches", [])
        gaps = available_resources.get("gaps", [])
        print(f"    Found {len(matches)} match(es), {len(gaps)} gap(s)")
    except Exception as e:
        print(f"    JSON parse failed ({e}) — using empty resources")
        available_resources = {"matches": [], "gaps": []}

    return {
        "available_resources": available_resources,
        "capacity_context": capacity_context
    }


# ============================================================
# NODE 3 — CONFIGURE PACKAGE
# Input:  requirements, available_resources, retry_feedback (if retry)
# Output: package_config (proposed team composition)
#
# On first run: picks the best team from available resources.
# On retry:     includes retry_feedback so LLM knows what to fix
#               (e.g., "margin too low — reduce team size or swap to junior")
# ============================================================

def configure_package_node(state: SalesQuoteState) -> dict:
    retry_count = state.get("retry_count", 0)
    print(f"\n--- Node 3: configure_package_node (attempt {retry_count + 1}) ---")

    llm = get_llm()

    # On retry, inject the feedback so the LLM knows what went wrong
    if retry_count > 0:
        retry_section = f"""
IMPORTANT — Previous configuration failed policy validation.
Feedback from pricing check: {state.get('retry_feedback', '')}
You MUST adjust the team to fix this issue.
"""
    else:
        retry_section = ""

    # Fill the {retry_section} placeholder in the prompt
    prompt = CONFIGURE_PACKAGE_PROMPT.format(retry_section=retry_section)

    response = llm.invoke([
        SystemMessage(content=prompt),
        HumanMessage(content=f"""
{date_context()}
CLIENT REQUIREMENTS:
{json.dumps(state["requirements"], indent=2, ensure_ascii=False)}

AVAILABLE RESOURCES (from capacity check):
{json.dumps(state["available_resources"], indent=2, ensure_ascii=False)}
""")
    ])

    try:
        package_config = parse_llm_json(response)
        team = package_config.get("team", [])
        print(f"    Configured team of {len(team)} person(s)")
        for member in team:
            print(f"      - {member.get('name')} ({member.get('role')})")
    except Exception as e:
        print(f"    JSON parse failed ({e}) — using empty config")
        package_config = {"team": [], "rationale": "", "warnings": []}

    return {"package_config": package_config}


# ============================================================
# NODE 4 — PRICING & POLICY VALIDATION
# Input:  requirements, package_config
# Output: pricing_result, policy_valid, retry_count, retry_feedback
#
# How it works:
# 1. Search the pricing policy RAG for rate cards and rules
# 2. Ask LLM to calculate full pricing + check margin policy
# 3. If policy fails → set retry_feedback and increment retry_count
#    The conditional edge will then loop back to Node 3.
# ============================================================

def pricing_and_policy_node(state: SalesQuoteState) -> dict:
    print("\n--- Node 4: pricing_and_policy_node ---")

    requirements = state["requirements"]
    package_config = state["package_config"]
    search_tool = create_pricing_retriever_tool()

    # Search for relevant pricing rules
    # Build a query from the roles in the proposed team
    team = package_config.get("team", [])
    roles_in_team = list(set([m.get("role", "") for m in team]))
    pricing_query = f"rate card discount margin {' '.join(roles_in_team[:3])}"

    print(f"    Searching pricing policy for: '{pricing_query}'")
    pricing_context = search_tool.invoke(pricing_query)

    # Also fetch general discount and margin rules
    policy_context = search_tool.invoke("discount margin minimum approval")

    llm = get_llm()
    response = llm.invoke([
        SystemMessage(content=PRICING_PROMPT),
        HumanMessage(content=f"""
CLIENT REQUIREMENTS:
{json.dumps(requirements, indent=2, ensure_ascii=False)}

PROPOSED TEAM:
{json.dumps(package_config, indent=2, ensure_ascii=False)}

PRICING POLICY (retrieved from database):
{pricing_context}

{policy_context}
""")
    ])

    try:
        pricing_result = parse_llm_json(response)
        margin = pricing_result.get("gross_margin_pct", 0)
        policy_passed = pricing_result.get("policy_passed", False)
        policy_notes = pricing_result.get("policy_notes", "")
        total = pricing_result.get("total_after_discount_usd", 0)
        print(f"    Total: ${total:,.0f} | Margin: {margin}% | Policy: {'PASS' if policy_passed else 'FAIL'}")
    except Exception as e:
        print(f"    JSON parse failed ({e}) — defaulting to policy fail")
        pricing_result = {"policy_passed": False, "gross_margin_pct": 0, "policy_notes": str(e)}
        policy_passed = False
        margin = 0
        policy_notes = str(e)

    # If policy failed and we still have retries left → set feedback for Node 3
    current_retry_count = state.get("retry_count", 0)

    if not policy_passed:
        feedback = (
            f"Pricing failed policy: {policy_notes}. "
            f"Current margin is {margin}%. "
            "Consider: reduce team size, swap senior roles to mid, "
            "remove tentative/optional roles, or increase engagement duration for better discount."
        )
        print(f"    Setting retry feedback: {feedback}")
        return {
            "pricing_result": pricing_result,
            "policy_valid": False,
            "retry_count": current_retry_count + 1,
            "retry_feedback": feedback
        }

    # Policy passed — no retry needed
    return {
        "pricing_result": pricing_result,
        "policy_valid": True,
        "retry_feedback": ""
    }


# ============================================================
# NODE 5 — GENERATE OUTPUT
# Input:  requirements, package_config, pricing_result, retry_count
# Output: final_output (formatted string for the sales team)
#
# Only reached when policy passes OR max retries is hit.
# ============================================================

def generate_output_node(state: SalesQuoteState) -> dict:
    print("\n--- Node 5: generate_output_node ---")
    llm = get_llm()

    retry_count = state.get("retry_count", 0)
    policy_valid = state.get("policy_valid", False)

    # Include a note if we hit max retries without passing policy
    retry_note = ""
    if not policy_valid:
        retry_note = f"\nNOTE: This quote did not fully pass margin policy after {retry_count} retry attempt(s). Flag for manual review.\n"

    response = llm.invoke([
        SystemMessage(content=OUTPUT_PROMPT),
        HumanMessage(content=f"""
ORIGINAL INPUT:
{state["raw_input"]}

EXTRACTED REQUIREMENTS:
{json.dumps(state["requirements"], indent=2, ensure_ascii=False)}

PROPOSED TEAM:
{json.dumps(state["package_config"], indent=2, ensure_ascii=False)}

PRICING RESULT:
{json.dumps(state["pricing_result"], indent=2, ensure_ascii=False)}

POLICY STATUS: {"PASSED" if policy_valid else "FAILED (max retries reached)"}
RETRIES NEEDED: {retry_count}
{retry_note}
""")
    ])

    # Extract the text from the response
    if isinstance(response.content, list):
        final_output = response.content[0].get("text", "") if response.content else ""
    else:
        final_output = response.content

    print("    Final output generated.")
    return {"final_output": final_output}


# ============================================================
# CONDITIONAL EDGE FUNCTION
# Decides what happens after Node 4 (pricing & policy check).
# This is what creates the retry loop — it can go BACKWARD.
# ============================================================

MAX_RETRIES = 2

def route_after_pricing(state: SalesQuoteState) -> str:
    if state.get("policy_valid"):
        # Policy passed — move forward to final output
        return "generate_output_node"

    elif state.get("retry_count", 0) >= MAX_RETRIES:
        # Too many retries — give up and generate output anyway
        print(f"    Max retries ({MAX_RETRIES}) reached — proceeding to output")
        return "generate_output_node"

    else:
        # Policy failed and retries remaining — loop back to Node 3
        print(f"    Retry {state.get('retry_count')}/{MAX_RETRIES} — looping back to configure")
        return "configure_package_node"
