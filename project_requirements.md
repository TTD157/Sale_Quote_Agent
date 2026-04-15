# Project Requirements Document
## AI Agent: Hỗ trợ cấu hình gói dịch vụ & pricing theo policy

> POC Project — Sales Support for IT Outsourcing Company

---

## 1. Business Context

### 1.1 Company Context
An IT outsourcing company that provides software development teams to clients. The company does **not** have fixed service packages — each engagement is assembled dynamically based on current delivery team capacity and client needs.

### 1.2 Current Workflow (Pain Point)
The sales department works **cross-functionally with the delivery department** to assemble quotes for clients:

1. Salesperson receives client needs through various channels (meetings, emails, Slack, calls)
2. Information is **unstructured and messy** — meeting notes, forwarded emails, quick messages
3. Sales manually extracts what the client wants
4. Sales asks delivery team: "Who do we have available that fits?"
5. Delivery checks bench availability, skills, and timelines
6. Back-and-forth negotiation between sales and delivery to find the best fit
7. Sales applies pricing rules per company policy (rate cards, discounts, margins)
8. Sales assembles a quote and validates it against policy constraints

**Problem:** This process involves multiple people, multiple conversations, and is slow and error-prone.

### 1.3 What the Agent Does
The AI agent automates steps 3–8 by acting as a **bridge between sales and delivery**. The salesperson pastes raw, unstructured input and receives an actionable, policy-compliant quote with team recommendations.

---

## 2. Functional Requirements

### 2.1 Input Processing
- **FR-01**: Accept unstructured text input in Vietnamese, English, or mixed language
- **FR-02**: Support various input formats: meeting notes, email threads, Slack messages, forwarded messages, bullet points
- **FR-03**: Extract structured client requirements from noisy input including:
  - Client name (if mentioned)
  - Project domain/industry
  - Technology stack
  - Roles needed — distinguish between confirmed and tentative needs
  - Timeline (start date, duration)
  - Budget (range, flexibility signals)
  - Special requirements or preferences
  - Urgency level
  - Whether this is an existing or new client
- **FR-04**: Handle vague or incomplete information gracefully — mark as "not specified" or "tentative", never hallucinate

### 2.2 Delivery Capacity Matching
- **FR-05**: Search delivery team roster to find resources matching required skills, seniority, and availability
- **FR-06**: Classify matches as:
  - **Exact** — skills, seniority, and availability all match
  - **Close** — most criteria match, minor gaps (e.g., has React but not React Native)
  - **Substitute** — different seniority or needs ramp-up, but workable
- **FR-07**: Identify gaps where no suitable resource exists on the bench
- **FR-08**: Consider availability dates — flag conflicts with client's desired start date

### 2.3 Package Configuration (Reasoning)
- **FR-09**: Propose a concrete team composition — name specific people for each role
- **FR-10**: Reason about **best fit given current delivery reality**, not just what the client asked for
- **FR-11**: Suggest alternatives for gaps (e.g., "Person X has React experience, can ramp up on React Native in 2 weeks")
- **FR-12**: Consider budget constraints when configuring — if budget is tight, suggest skipping tentative roles or using junior alternatives
- **FR-13**: Consider team dynamics — recommend a senior lead if team is all juniors
- **FR-14**: If previous configuration failed policy check, adjust based on feedback (retry loop)

### 2.4 Pricing & Policy Validation
- **FR-15**: Apply correct rates from rate card based on role and seniority
- **FR-16**: Calculate applicable discounts:
  - Engagement duration discount
  - Team size discount
  - Multiplicative stacking, capped at 25%
- **FR-17**: Handle special pricing: part-time allocation (60% of rate), ramp-up discount (50% for first 2 weeks), urgency premium (5%)
- **FR-18**: Calculate gross margin using internal cost estimates
- **FR-19**: Validate against policy constraints:
  - Minimum margin (30% standard, 20% strategic accounts)
  - Minimum engagement duration (3 months)
  - Seniority substitution rules (max 1 level downward)
  - Team composition recommendations (QA for 3+ devs, BA for 5+)
- **FR-20**: Flag required approvals (Sales Manager / Head of Sales / CEO depending on scenario)
- **FR-21**: If policy validation fails, loop back to reconfigure (max 2 retries)

### 2.5 Output Generation
- **FR-22**: Generate a structured, actionable summary including:
  - Client requirement recap
  - Proposed team with availability status (✅ / ⚠️ / ❌)
  - Pricing breakdown table with discounts and final total
  - Budget comparison
  - Policy compliance status
  - Recommendations and talking points for the client conversation
- **FR-23**: Output should be directly usable by the sales team — no further processing needed

---

## 3. Non-Functional Requirements

### 3.1 Demo / POC Constraints (from project rules)
- **NFR-01**: Must have a **visual UI** — Gradio or Streamlit recommended. **Terminal-only demo is NOT accepted.**
- **NFR-02**: Agent must have **at least 3 nodes** in the graph (excluding Start/End). Current design has **5 nodes**.
- **NFR-03**: May integrate additional tools (web search, database, calculator, etc.) to enhance capabilities
- **NFR-04**: Must use **Python** for implementation
- **NFR-05**: Must use **LangGraph** to build and compile the agent graph
- **NFR-06**: Must be able to **export/visualize the graph** to verify correctness of graph structure
- **NFR-07**: Reference: https://docs.langchain.com/oss/python/langgraph/quickstart#6-build-and-compile-the-agent

### 3.2 Technical
- **NFR-08**: RAG-based retrieval for both delivery capacity and pricing policy
- **NFR-09**: Concentrated, focused POC — not rambling, demonstrate the core value clearly
- **NFR-10**: Support Vietnamese/English mixed input and output

---

## 4. Data Requirements

### 4.1 Delivery Team Roster (Knowledge Base)
Mock data representing current company state:

| Field            | Description                          | Example                        |
| ---------------- | ------------------------------------ | ------------------------------ |
| employee_id      | Unique identifier                    | EMP001                         |
| name             | Full name (Vietnamese)               | Nguyễn Văn Hùng                |
| role             | Job role                             | Backend Developer              |
| seniority        | Junior / Mid / Senior                | Senior (5 years)               |
| skills           | Technology skills                    | Node.js, TypeScript, AWS       |
| current_status   | Available / Assigned to project      | Assigned to Project Omega      |
| available_from   | When available for new work          | 2026-05-15                     |
| notes            | Additional context                   | Team lead experience           |

**Dataset size**: 15 employees across roles (Backend, Frontend, Mobile, QA, DevOps, BA)
**Key design**: Mix of available and committed resources to force the agent to reason about constraints

### 4.2 Pricing Policy (Knowledge Base)
| Section              | Content                                                    |
| -------------------- | ---------------------------------------------------------- |
| Rate cards           | Monthly rates by role × seniority (Junior/Mid/Senior)      |
| Duration discounts   | 0% (<3mo), 5% (3-5mo), 10% (6-11mo), 15% (12+mo)         |
| Team size discounts  | 0% (1-2), 3% (3-5), 5% (6-9), 8% (10+)                   |
| Discount cap         | Max combined discount: 25%                                  |
| Margin rules         | Min 30% standard, 20% strategic (needs approval)           |
| Internal cost        | Junior 55%, Mid 58%, Senior 60% of standard rate           |
| Engagement terms     | Min 3 months, exceptions for 3+ person teams               |
| Substitution rules   | Max 1 level down, with rate adjustments                    |
| Special pricing      | Part-time (60% rate), ramp-up (50% for 2 weeks), urgency (+5%) |
| Approval matrix      | Escalation thresholds by discount level and margin         |

### 4.3 Test Inputs (5 scenarios)
| #  | Scenario                    | What It Tests                                              |
| -- | --------------------------- | ---------------------------------------------------------- |
| 1  | E-commerce meeting notes    | Messy Vietnamese input, tentative requirements, e-commerce domain |
| 2  | Fintech startup email       | Tight budget ($20k), part-time DevOps, Java stack          |
| 3  | Quick Slack message          | Short message, existing client, extending a current team   |
| 4  | Healthcare messy notes      | Vague requirements ("whatever you recommend"), no tech preference |
| 5  | Urgent staffing email       | Start THIS WEEK, strategic account, urgency premium        |

---

## 5. Architecture

### 5.1 Tech Stack
| Component        | Technology                    |
| ---------------- | ----------------------------- |
| Agent Framework  | LangChain + LangGraph         |
| LLM              | OpenAI GPT-4o-mini            |
| Embeddings       | OpenAI text-embedding-3-small |
| Vector Store     | ChromaDB (2 collections)      |
| UI               | Gradio                        |
| Language          | Python                        |

### 5.2 Agent Graph (LangGraph — 5 Nodes + Conditional Edge)

```
[START] ← raw meeting notes / email / message
   │
   ▼
┌─────────────────────────────┐
│  Node 1: Extract            │
│  Requirements               │  LLM: parse messy input → structured JSON
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│  Node 2: Check Delivery     │
│  Capacity                   │  RAG: search team roster → matching resources
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│  Node 3: Reason &           │
│  Configure Package          │  LLM: best-fit team + gap analysis
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│  Node 4: Apply Pricing      │
│  & Policy Check             │  RAG + LLM: pricing calc + validation
└──────────┬──────────────────┘
           │
       ┌───┴────┐
       │ Valid?  │ ← conditional edge
       └───┬────┘
      yes  │  no → back to Node 3 (max 2 retries)
           ▼
┌─────────────────────────────┐
│  Node 5: Generate Output    │  LLM: final structured summary
└─────────────────────────────┘
           │
        [END]
```

### 5.3 Tools Used by Agent
| Tool                       | Used By    | Purpose                                           |
| -------------------------- | ---------- | ------------------------------------------------- |
| search_delivery_capacity   | Node 2     | RAG retriever — search team roster by skills/role  |
| search_pricing_policy      | Node 4     | RAG retriever — search pricing docs by query       |

### 5.4 State (Shared Across All Nodes)
| Field               | Type   | Set By  | Description                              |
| ------------------- | ------ | ------- | ---------------------------------------- |
| raw_input           | str    | Input   | Original unstructured text               |
| requirements        | dict   | Node 1  | Structured client requirements (JSON)    |
| available_resources | dict   | Node 2  | Matched resources + gaps                 |
| capacity_context    | str    | Node 2  | Raw retrieved roster docs                |
| package_config      | dict   | Node 3  | Proposed team composition                |
| pricing_result      | dict   | Node 4  | Pricing breakdown + policy check         |
| policy_valid        | bool   | Node 4  | Whether policy validation passed         |
| retry_count         | int    | Node 4  | Number of retry attempts (max 2)         |
| retry_feedback      | str    | Node 4  | Feedback for Node 3 on what to adjust    |
| final_output        | str    | Node 5  | Final formatted summary for sales team   |

---

## 6. Key Agent Reasoning Capabilities

What makes this more than a lookup tool — the agent makes judgment calls:

1. **Fuzzy input handling** — extracts structure from messy human notes, distinguishes confirmed vs. tentative needs
2. **Best-fit matching** — "we don't have an exact match but person X is close enough, here's why"
3. **Gap identification** — "no React Native dev on bench → suggest Frontend dev with React experience + ramp-up"
4. **Budget awareness** — "if we include tentative QA, we're still under budget, so recommend it"
5. **Timeline conflict detection** — "person A not free until May 15 but client wants to start next month"
6. **Policy compliance** — automatic margin check, discount cap, engagement minimum, approval routing
7. **Self-correction** — if pricing fails policy, loops back to reconfigure with specific feedback

---

## 7. In-Scope vs. Out-of-Scope Summary

| Feature                                          | Status        |
| ------------------------------------------------ | ------------- |
| Unstructured input processing (VN/EN mix)        | ✅ In-scope    |
| Delivery capacity matching via RAG               | ✅ In-scope    |
| Best-fit reasoning with gap analysis             | ✅ In-scope    |
| Pricing calculation with discounts               | ✅ In-scope    |
| Policy validation with retry loop                | ✅ In-scope    |
| Structured output for sales team                 | ✅ In-scope    |
| Visual UI (Gradio)                               | ✅ In-scope    |
| Graph visualization export                       | ✅ In-scope    |
| 5 sample test scenarios                          | ✅ In-scope    |
| Real-time HR/resource system sync                | ❌ Out-of-scope |
| Contract/proposal document generation            | ❌ Out-of-scope |
| Client-facing chatbot                            | ❌ Out-of-scope |
| CRM integration                                  | ❌ Out-of-scope |
| Approval workflows                               | ❌ Out-of-scope |
| Multi-turn conversation / negotiation            | ❌ Out-of-scope |
| E-signature / legal documents                    | ❌ Out-of-scope |

---

## 8. Demo Checklist

| #   | Requirement                                             | Status |
| --- | ------------------------------------------------------- | ------ |
| 1   | Visual UI (Gradio/Streamlit) — NOT terminal             | ✅      |
| 2   | At least 3 agent nodes (excl. Start/End)                | ✅ (5)  |
| 3   | Tool integration (RAG retrievers)                       | ✅ (2)  |
| 4   | Python implementation                                   | ✅      |
| 5   | LangGraph for graph build & compile                     | ✅      |
| 6   | Export graph to verify structure                         | ✅      |
| 7   | Correct graph structure between nodes                   | ✅      |

---

*Last updated: April 9, 2026*
