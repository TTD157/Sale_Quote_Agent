# ============================================================
# ui/app.py  —  Sales Quote Agent  (redesigned UI/UX)
# ============================================================

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import uuid
import datetime
import pandas as pd
import gradio as gr

from agents.sales_quote.graph import build_sales_quote_graph

# ── Start-up ─────────────────────────────────────────────────
print("Loading agent graph...")
_app = build_sales_quote_graph()
print("Agent ready.")

# ── Paths ─────────────────────────────────────────────────────
BASE      = os.path.join(os.path.dirname(__file__), "..")
GRAPH_IMG = os.path.join(BASE, "storage", "graph_visualization.png")
ROSTER    = os.path.join(BASE, "data", "documents", "delivery_roster.txt")
POLICY    = os.path.join(BASE, "data", "documents", "pricing_policy.txt")

# ── Sample inputs ─────────────────────────────────────────────
EXAMPLES = {
    "Scenario 1 — E-commerce (Vietnamese)": (
        "Anh ơi, hôm nay em vừa gặp khách hàng TechMart, họ đang muốn build lại hệ thống e-commerce.\n"
        "Cần khoảng 2 backend senior (React Node.js), 1 frontend mid, và có thể thêm 1 QA nếu budget cho phép.\n"
        "Timeline họ muốn bắt đầu tháng 6, khoảng 8 tháng. Budget họ chưa confirm nhưng nói flexible.\n"
        "Khách hàng mới nhé anh."
    ),
    "Scenario 2 — Fintech tight budget (English)": (
        "Hi team, just got off a call with FinPay fintech startup.\n"
        "They need: 2 mid backend devs (Java/Spring Boot), 1 React frontend, 1 part-time DevOps.\n"
        "Budget MAX $20,000/month total — very firm on this.\n"
        "Start: June 1, 6 months. New client, high growth potential."
    ),
    "Scenario 3 — Existing client team extension": (
        "@sales — VinGroup just pinged. They want to extend their current team.\n"
        "Need 1 more senior backend (Node.js preferred) starting next month.\n"
        "Happy with current team, just scaling up. Existing client. 3-4 months extension.\n"
        "No hard budget constraint mentioned."
    ),
    "Scenario 4 — Healthcare vague requirements": (
        "Meeting notes — HealthBridge hospital system.\n"
        "Client wants to digitize patient management. No internal tech team.\n"
        "Said 'whatever you recommend' for tech stack. Probably frontend + backend + maybe mobile?\n"
        "Budget ~$15k/month, 12 month project. Start ASAP. New client."
    ),
    "Scenario 5 — Urgent strategic account": (
        "URGENT — FPT Software (strategic partner) needs 1 senior fullstack dev THIS WEEK.\n"
        "React + Node.js. Current dev had emergency, project deadline in 6 weeks.\n"
        "Needs someone who can hit the ground running — no ramp-up time.\n"
        "FPT account = $500k+ historical revenue."
    ),
}

# ─────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────

def load_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def roster_stats_line(text: str) -> str:
    available = text.count("Current Status: Available")
    assigned  = text.count("Current Status: Assigned")
    return (
        f"🟢 **{available}** available now &nbsp;·&nbsp; "
        f"🔴 **{assigned}** on project &nbsp;·&nbsp; "
        f"👥 **{available + assigned}** total"
    )


def parse_roster(text: str) -> pd.DataFrame:
    """Parse the roster .txt into a DataFrame — one row per employee."""
    employees, current = [], {}
    for line in text.splitlines():
        line = line.strip()
        if not line or set(line) <= {"=", "-", " "}:
            continue
        if line.startswith("EMPLOYEE:"):
            if current.get("Name"):
                employees.append(current)
            current = {"ID": line.split(":", 1)[1].strip()}
        elif ":" in line and current:
            key, _, val = line.partition(":")
            key = key.strip(); val = val.strip()
            field_map = {
                "Name": "Name", "Role": "Role", "Seniority": "Seniority",
                "Skills": "Skills", "Current Status": "Status",
                "Available From": "Available From", "Notes": "Notes",
            }
            if key in field_map:
                current[field_map[key]] = val
    if current.get("Name"):
        employees.append(current)
    cols = ["ID", "Name", "Role", "Seniority", "Skills", "Status", "Available From", "Notes"]
    return pd.DataFrame(employees, columns=cols).fillna("")


def df_to_roster_text(df: pd.DataFrame) -> str:
    """Convert an edited DataFrame back into the .txt roster format."""
    lines = [
        "DELIVERY TEAM ROSTER",
        f"Last updated: {datetime.date.today().isoformat()}",
        "Company: Rikkei Software",
        "",
    ]
    for _, row in df.iterrows():
        lines += [
            "=" * 64, "",
            f"EMPLOYEE: {row.get('ID', '')}",
            f"Name: {row.get('Name', '')}",
            f"Role: {row.get('Role', '')}",
            f"Seniority: {row.get('Seniority', '')}",
            f"Skills: {row.get('Skills', '')}",
            f"Current Status: {row.get('Status', '')}",
            f"Available From: {row.get('Available From', '')}",
            f"Notes: {row.get('Notes', '')}",
            "", "---", "",
        ]
    return "\n".join(lines)


def _reindex(file_path: str, collection_name: str) -> tuple:
    """Delete old ChromaDB collection and rebuild from file.
       Returns (success: bool, n_chunks: int, error: str)."""
    try:
        from langchain_community.document_loaders import TextLoader
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        from langchain_community.vectorstores import Chroma
        from core.llm import get_embeddings
        from config.settings import CHROMA_DB_PATH

        old = Chroma(persist_directory=CHROMA_DB_PATH,
                     embedding_function=get_embeddings(),
                     collection_name=collection_name)
        old.delete_collection()

        docs   = TextLoader(file_path, encoding="utf-8").load()
        chunks = RecursiveCharacterTextSplitter(
                     chunk_size=500, chunk_overlap=50
                 ).split_documents(docs)
        Chroma.from_documents(documents=chunks, embedding=get_embeddings(),
                              persist_directory=CHROMA_DB_PATH,
                              collection_name=collection_name)
        return True, len(chunks), ""
    except Exception as e:
        return False, 0, str(e)


# ─────────────────────────────────────────────────────────────
# AGENT RUNNER  (generator — streams node updates)
# ─────────────────────────────────────────────────────────────

def run_agent(raw_input: str):
    if not raw_input or not raw_input.strip():
        gr.Warning("Please enter sales notes before generating a quote.")
        yield "*Waiting for input...*", "*Output will appear here.*"
        return

    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    state  = {
        "raw_input": raw_input.strip(),
        "requirements": {}, "available_resources": {},
        "capacity_context": "", "package_config": {},
        "pricing_result": {}, "policy_valid": False,
        "retry_count": 0, "retry_feedback": "", "final_output": "",
    }

    NODE_LABELS = {
        "extract_requirements_node": "Node 1 — Extracting requirements",
        "check_capacity_node":       "Node 2 — Checking delivery capacity",
        "configure_package_node":    "Node 3 — Configuring team package",
        "pricing_and_policy_node":   "Node 4 — Pricing & policy check",
        "generate_output_node":      "Node 5 — Generating final output",
    }

    log_lines    = []
    final_output = ""

    for update in _app.stream(state, config=config, stream_mode="updates"):
        for node_name, node_output in update.items():
            label = NODE_LABELS.get(node_name, node_name)

            if node_name == "extract_requirements_node":
                r = node_output.get("requirements", {})
                detail = f"Client: **{r.get('client_name','unknown')}** · {len(r.get('roles_needed',[]))} role(s)"
            elif node_name == "check_capacity_node":
                res = node_output.get("available_resources", {})
                detail = f"{len(res.get('matches',[]))} match(es) · {len(res.get('gaps',[]))} gap(s)"
            elif node_name == "configure_package_node":
                t = node_output.get("package_config", {}).get("team", [])
                detail = f"Team of {len(t)} configured"
            elif node_name == "pricing_and_policy_node":
                p = node_output.get("pricing_result", {})
                passed = node_output.get("policy_valid", False)
                status = "✅ PASS" if passed else "🔄 FAIL — retrying"
                detail = f"Total: ${p.get('total_after_discount_usd',0):,.0f} · Margin: {p.get('gross_margin_pct',0):.1f}% · {status}"
            elif node_name == "generate_output_node":
                detail        = "Complete"
                final_output  = node_output.get("final_output", "")
            else:
                detail = ""

            log_lines.append(f"**{label}**  \n`{detail}`")
            yield "\n\n".join(log_lines), ""

    yield "\n\n".join(log_lines) + "\n\n---\n✅ **Done.**", final_output


# ─────────────────────────────────────────────────────────────
# ROSTER  save / reload
# ─────────────────────────────────────────────────────────────

def save_roster_table(df: pd.DataFrame):
    """Save edited DataFrame → .txt → re-index. Toast on result."""
    text = df_to_roster_text(df)
    with open(ROSTER, "w", encoding="utf-8") as f:
        f.write(text)
    ok, n, err = _reindex(ROSTER, "delivery_roster")
    if ok:
        gr.Info(f"Roster saved & re-indexed — {n} chunks stored.")
    else:
        gr.Warning(f"Save failed: {err}")
    updated = load_file(ROSTER)
    return parse_roster(updated), roster_stats_line(updated), updated


def reload_roster():
    text = load_file(ROSTER)
    return parse_roster(text), roster_stats_line(text), text, "_Reloaded from disk._"


def add_empty_row(df: pd.DataFrame) -> pd.DataFrame:
    """Append a blank employee row so the user can fill it in directly."""
    # Auto-generate the next employee ID based on current count
    next_num = len(df) + 1
    new_row = {
        "ID":             f"EMP{next_num:03d}",
        "Name":           "",
        "Role":           "",
        "Seniority":      "",
        "Skills":         "",
        "Status":         "Available",
        "Available From": datetime.date.today().isoformat(),
        "Notes":          "",
    }
    return pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)


def save_roster_raw(text: str):
    with open(ROSTER, "w", encoding="utf-8") as f:
        f.write(text)
    ok, n, err = _reindex(ROSTER, "delivery_roster")
    if ok:
        gr.Info(f"Roster saved & re-indexed — {n} chunks stored.")
    else:
        gr.Warning(f"Save failed: {err}")
    return parse_roster(text), roster_stats_line(text)


# ─────────────────────────────────────────────────────────────
# POLICY  save / reload
# ─────────────────────────────────────────────────────────────

def save_policy(text: str):
    with open(POLICY, "w", encoding="utf-8") as f:
        f.write(text)
    ok, n, err = _reindex(POLICY, "pricing_policy")
    if ok:
        gr.Info(f"Policy saved & re-indexed — {n} chunks stored.")
    else:
        gr.Warning(f"Save failed: {err}")
    return text   # refresh the preview


def reload_policy():
    return load_file(POLICY)


# ─────────────────────────────────────────────────────────────
# CUSTOM CSS  —  corporate blue / slate theme
# ─────────────────────────────────────────────────────────────

CSS = """
/* ── Global ──────────────────────────────────────────── */
.gradio-container {
    max-width: 1440px !important;
    margin: 0 auto !important;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    background: #f1f5f9 !important;
}

/* ── Header banner ───────────────────────────────────── */
#app-header {
    background: linear-gradient(120deg, #1e3a5f 0%, #2563eb 100%);
    border-radius: 14px;
    padding: 28px 36px;
    margin-bottom: 20px;
    box-shadow: 0 4px 20px rgba(37,99,235,0.25);
}
#app-header h1 { color: #ffffff !important; font-size: 26px !important;
                 font-weight: 700 !important; margin: 0 0 6px 0 !important; }
#app-header p  { color: #bfdbfe !important; font-size: 14px !important;
                 margin: 0 !important; }

/* ── Tab bar ─────────────────────────────────────────── */
.tabs > .tab-nav {
    background: #ffffff !important;
    border-radius: 10px 10px 0 0 !important;
    border-bottom: 2px solid #e2e8f0 !important;
    padding: 0 16px !important;
}
.tabs > .tab-nav > button {
    font-size: 14px !important; font-weight: 500 !important;
    padding: 12px 20px !important; border-radius: 0 !important;
    color: #64748b !important;
}
.tabs > .tab-nav > button.selected {
    color: #2563eb !important;
    border-bottom: 2px solid #2563eb !important;
    font-weight: 600 !important;
}

/* ── Tab content panel ───────────────────────────────── */
.tabitem {
    background: #ffffff !important;
    border-radius: 0 0 10px 10px !important;
    padding: 24px !important;
    border: 1px solid #e2e8f0 !important;
    border-top: none !important;
}

/* ── Generate button (bold primary) ─────────────────── */
#generate-btn {
    background: #2563eb !important;
    color: #ffffff !important;
    font-size: 15px !important;
    font-weight: 700 !important;
    border-radius: 8px !important;
    height: 48px !important;
    letter-spacing: 0.4px !important;
    box-shadow: 0 2px 8px rgba(37,99,235,0.3) !important;
    border: none !important;
}
#generate-btn:hover { background: #1d4ed8 !important; }

/* ── Secondary buttons (outlined) ───────────────────── */
#clear-btn, #save-btn, #reload-btn {
    background: #ffffff !important;
    color: #374151 !important;
    border: 1.5px solid #d1d5db !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    height: 44px !important;
}
#clear-btn:hover, #reload-btn:hover { border-color: #2563eb !important; color: #2563eb !important; }
#save-btn { color: #059669 !important; border-color: #059669 !important; }
#save-btn:hover { background: #ecfdf5 !important; }

/* ── Input & output textboxes ────────────────────────── */
.input-panel textarea {
    border: 1.5px solid #e2e8f0 !important;
    border-radius: 8px !important;
    font-size: 14px !important;
    line-height: 1.6 !important;
    padding: 12px !important;
}
.input-panel textarea:focus { border-color: #2563eb !important; }

/* placeholder — real CSS injected via gr.HTML inside the Blocks context */

/* ── Section labels ──────────────────────────────────── */
.section-label {
    font-size: 12px !important;
    font-weight: 600 !important;
    color: #64748b !important;
    text-transform: uppercase !important;
    letter-spacing: 0.8px !important;
    margin-bottom: 8px !important;
}

/* ── Accordion ───────────────────────────────────────── */
.accordion-header {
    background: #f8fafc !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 8px !important;
}

/* ── Stat badges in roster ───────────────────────────── */
#roster-stats { font-size: 14px !important; padding: 8px 0 12px 0 !important; }

/* ── Dropdown for examples ───────────────────────────── */
#example-dropdown { font-size: 14px !important; }

/* ── Admin sub-tabs ──────────────────────────────────── */
.admin-tabs > .tab-nav {
    background: #f8fafc !important;
    border-radius: 8px 8px 0 0 !important;
    padding: 0 12px !important;
}
.admin-tabs > .tab-nav > button { font-size: 13px !important; padding: 8px 16px !important; }
"""


# ─────────────────────────────────────────────────────────────
# BUILD UI
# ─────────────────────────────────────────────────────────────

_roster_text  = load_file(ROSTER)
_policy_text  = load_file(POLICY)

with gr.Blocks(title="Sales Quote Agent") as demo:

    # ── Inject CSS via HTML (launch(css=) is broken in Gradio 6) ──
    gr.HTML("""<style>
    /* Quote output box — fixed height, scroll internally */
    #quote-output {
        max-height: 620px !important;
        overflow-y: auto !important;
        overflow-x: hidden !important;
    }
    /* Quote output — wrap all markdown content */
    [data-testid="markdown"] {
        overflow-wrap: break-word !important;
        word-break: break-word !important;
        white-space: normal !important;
        max-width: 100% !important;
    }
    [data-testid="markdown"] table {
        width: 100% !important;
        table-layout: fixed !important;
        border-collapse: collapse !important;
        display: table !important;
    }
    [data-testid="markdown"] th,
    [data-testid="markdown"] td {
        overflow-wrap: break-word !important;
        word-break: break-word !important;
        white-space: normal !important;
        padding: 6px 10px !important;
        border: 1px solid #e2e8f0 !important;
        vertical-align: top !important;
    }
    /* Raw text editors: fixed height + internal scroll */
    #roster-raw-editor textarea,
    #policy-raw-editor textarea {
        height: 480px !important;
        max-height: 480px !important;
        overflow-y: scroll !important;
        overflow-x: auto !important;
        resize: vertical !important;
        font-family: 'Consolas', 'Monaco', monospace !important;
        font-size: 13px !important;
        line-height: 1.55 !important;
    }
    /* Header banner */
    #app-header {
        background: linear-gradient(120deg, #1e3a5f 0%, #2563eb 100%);
        border-radius: 14px; padding: 28px 36px; margin-bottom: 20px;
        box-shadow: 0 4px 20px rgba(37,99,235,0.25);
    }
    #app-header h1 { color: #fff !important; font-size: 26px !important; font-weight: 700 !important; margin: 0 0 6px 0 !important; }
    #app-header p  { color: #bfdbfe !important; font-size: 14px !important; margin: 0 !important; }
    /* Primary generate button */
    #generate-btn { background: #2563eb !important; color: #fff !important; font-size: 15px !important;
                    font-weight: 700 !important; border-radius: 8px !important; height: 48px !important;
                    box-shadow: 0 2px 8px rgba(37,99,235,0.3) !important; border: none !important; }
    #generate-btn:hover { background: #1d4ed8 !important; }
    /* Secondary buttons */
    #clear-btn, #save-btn, #reload-btn {
        background: #fff !important; color: #374151 !important;
        border: 1.5px solid #d1d5db !important; border-radius: 8px !important;
        font-weight: 500 !important; height: 44px !important;
    }
    #save-btn { color: #059669 !important; border-color: #059669 !important; }
    </style>""")

    # ── Header ────────────────────────────────────────────────
    gr.HTML("""
    <div id="app-header">
        <h1>Sales Quote Agent</h1>
        <p>IT Outsourcing · Sales Support Tool &nbsp;|&nbsp;
           Paste raw sales notes in Vietnamese, English, or mixed — get a policy-compliant quote instantly.</p>
    </div>
    """)

    with gr.Tabs():

        # ══════════════════════════════════════════════════════
        # TAB 1 — QUOTE GENERATOR  (sales-facing, clean)
        # ══════════════════════════════════════════════════════
        with gr.TabItem("📋  Quote Generator"):
            with gr.Row(equal_height=False):

                # ── LEFT: Input area ──────────────────────────
                with gr.Column(scale=1, elem_classes="input-panel"):
                    gr.Markdown("**Sales Notes**", elem_classes="section-label")
                    input_box = gr.Textbox(
                        placeholder=(
                            "Paste your meeting notes, email, or Slack message here…\n\n"
                            "e.g. 'Vừa gặp khách TechMart, cần 2 backend senior Node.js, "
                            "budget flexible, start tháng 6...'"
                        ),
                        lines=10,
                        max_lines=18,
                        show_label=False,
                    )

                    # Example picker — dropdown instead of 5 buttons
                    example_dd = gr.Dropdown(
                        choices=["— Load an example —"] + list(EXAMPLES.keys()),
                        value="— Load an example —",
                        label="Try a sample scenario",
                        elem_id="example-dropdown",
                    )

                    with gr.Row():
                        gen_btn   = gr.Button("Generate Quote", variant="primary",
                                              elem_id="generate-btn", scale=3)
                        clear_btn = gr.Button("Clear", elem_id="clear-btn", scale=1)

                # ── RIGHT: Output area ────────────────────────
                with gr.Column(scale=1):
                    gr.Markdown("**Quote Output**", elem_classes="section-label")
                    output_box = gr.Markdown(
                        value="*Your generated quote will appear here.*",
                        elem_id="quote-output",
                    )

                    # Processing log — collapsed by default so it doesn't distract
                    with gr.Accordion("Processing Log", open=False):
                        log_box = gr.Markdown(value="*Waiting for input…*")

            # ── Button wiring ─────────────────────────────────
            gen_btn.click(
                fn=run_agent,
                inputs=input_box,
                outputs=[log_box, output_box],
            )
            clear_btn.click(
                fn=lambda: ("", "*Waiting for input…*", "*Your generated quote will appear here.*"),
                outputs=[input_box, log_box, output_box],
            )
            example_dd.change(
                fn=lambda choice: EXAMPLES.get(choice, ""),
                inputs=example_dd,
                outputs=input_box,
            )

        # ══════════════════════════════════════════════════════
        # TAB 2 — ADMIN  (technical / management area)
        # ══════════════════════════════════════════════════════
        with gr.TabItem("⚙️  Admin"):
            with gr.Tabs(elem_classes="admin-tabs"):

                # ── Admin sub-tab A: Team Roster ──────────────
                with gr.TabItem("👥  Team Roster"):
                    gr.Markdown("### Delivery Team Roster")

                    # Live stats bar
                    roster_stats_md = gr.Markdown(
                        roster_stats_line(_roster_text),
                        elem_id="roster-stats",
                    )

                    # Editable table — primary editing interface
                    # interactive=True lets users edit cells directly (like Excel)
                    roster_table = gr.Dataframe(
                        value=parse_roster(_roster_text),
                        label="Current Team  (click any cell to edit)",
                        wrap=True,
                        interactive=True,
                    )
                    with gr.Row():
                        add_row_btn     = gr.Button("+ Add Employee", scale=1)
                        save_table_btn  = gr.Button("Save Changes", elem_id="save-btn", scale=2)
                        reload_tbl_btn  = gr.Button("Reload from Disk", elem_id="reload-btn", scale=1)

                    # Raw text editor — advanced / fallback option
                    with gr.Accordion("Advanced: Edit as Raw Text", open=False):
                        gr.Markdown(
                            "_Use this only if you need to add Notes or make bulk edits. "
                            "The table above is the recommended way to update the roster._"
                        )
                        roster_raw = gr.Textbox(
                            value=_roster_text, lines=25, max_lines=50,
                            label="delivery_roster.txt",
                            elem_id="roster-raw-editor",
                        )
                        with gr.Row():
                            save_raw_btn   = gr.Button("Save Raw Text", elem_id="save-btn", scale=2)
                            reload_raw_btn = gr.Button("Reload", elem_id="reload-btn", scale=1)

                    # Wiring — add empty row
                    add_row_btn.click(
                        fn=add_empty_row,
                        inputs=roster_table,
                        outputs=roster_table,
                    )

                    # Wiring — table save
                    save_table_btn.click(
                        fn=save_roster_table,
                        inputs=roster_table,
                        outputs=[roster_table, roster_stats_md, roster_raw],
                    )
                    reload_tbl_btn.click(
                        fn=reload_roster,
                        outputs=[roster_table, roster_stats_md, roster_raw],
                    )
                    # Wiring — raw text save
                    save_raw_btn.click(
                        fn=save_roster_raw,
                        inputs=roster_raw,
                        outputs=[roster_table, roster_stats_md],
                    )
                    reload_raw_btn.click(
                        fn=lambda: load_file(ROSTER),
                        outputs=roster_raw,
                    )

                # ── Admin sub-tab B: Pricing Policy ──────────
                with gr.TabItem("💰  Pricing Policy"):
                    gr.Markdown("### Pricing Policy & Rate Card")

                    # Read-only rendered preview
                    policy_preview = gr.Markdown(value=_policy_text)

                    with gr.Accordion("Edit Policy (raw text)", open=False):
                        gr.Markdown(
                            "_Edit below, then click **Save & Re-index** to apply changes immediately._"
                        )
                        policy_editor = gr.Textbox(
                            value=_policy_text, lines=25, max_lines=50,
                            label="pricing_policy.txt",
                            elem_id="policy-raw-editor",
                        )
                        with gr.Row():
                            save_pol_btn   = gr.Button("Save & Re-index", elem_id="save-btn", scale=2)
                            reload_pol_btn = gr.Button("Reload", elem_id="reload-btn", scale=1)

                    save_pol_btn.click(
                        fn=save_policy,
                        inputs=policy_editor,
                        outputs=policy_preview,
                    )
                    reload_pol_btn.click(
                        fn=reload_policy,
                        outputs=policy_editor,
                    )

                # ── Admin sub-tab C: Agent Graph ──────────────
                with gr.TabItem("🔗  Agent Graph"):
                    gr.Markdown("""
### Agent Graph Structure
The **dashed arrow** going upward from `pricing_and_policy_node` → `configure_package_node`
is the **retry loop** — triggered when the proposed team fails the 30% margin policy.
""")
                    if os.path.exists(GRAPH_IMG):
                        gr.Image(
                            value=GRAPH_IMG,
                            label="LangGraph — Sales Quote Agent",
                            interactive=False,
                            width=380,
                        )
                    else:
                        gr.Markdown("_Graph image not found. Run `python export_graph.py` first._")


# ── Launch ─────────────────────────────────────────────────────
if __name__ == "__main__":
    demo.launch(theme=gr.themes.Base(
        primary_hue=gr.themes.colors.blue,
        neutral_hue=gr.themes.colors.slate,
    ))
