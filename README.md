# Sale Quote Agent

An AI-powered sales support agent that automates the process of assembling team quotes for an IT outsourcing company. The salesperson pastes raw, unstructured client input (meeting notes, emails, Slack messages) and receives a structured, policy-compliant quote with team recommendations.

---

## What It Does

The traditional sales quoting process involves multiple back-and-forth conversations between sales and delivery teams. This agent automates that by:

1. **Extracting** structured requirements from messy, unstructured input (Vietnamese/English)
2. **Matching** available delivery team members to client needs via RAG search
3. **Configuring** the best-fit team composition with gap analysis
4. **Validating** pricing against company policy (discounts, margins, approval rules)
5. **Generating** a ready-to-use quote summary for the sales team

---

## Agent Architecture (LangGraph)

```
[START] ← raw meeting notes / email / message
   │
   ▼
┌─────────────────────────┐
│  Node 1: Extract        │  LLM: parse messy input → structured JSON
│  Requirements           │
└────────────┬────────────┘
             ▼
┌─────────────────────────┐
│  Node 2: Check Delivery │  RAG: search team roster → matching resources
│  Capacity               │
└────────────┬────────────┘
             ▼
┌─────────────────────────┐
│  Node 3: Reason &       │  LLM: best-fit team + gap analysis
│  Configure Package      │
└────────────┬────────────┘
             ▼
┌─────────────────────────┐
│  Node 4: Apply Pricing  │  RAG + LLM: pricing calc + policy validation
│  & Policy Check         │
└────────────┬────────────┘
         ┌───┴────┐
         │ Valid?  │ ← conditional edge (max 2 retries back to Node 3)
         └───┬────┘
             ▼
┌─────────────────────────┐
│  Node 5: Generate       │  LLM: final structured summary for sales team
│  Output                 │
└─────────────────────────┘
             │
          [END]
```

---

## Tech Stack

| Component       | Technology                        |
|----------------|-----------------------------------|
| Agent Framework | LangChain + LangGraph            |
| LLM             | OpenAI GPT-4o-mini               |
| Embeddings      | OpenAI text-embedding-3-small    |
| Vector Store    | ChromaDB (2 collections)         |
| UI              | Gradio                           |
| Language        | Python                           |

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/TTD157/Sale_Quote_Agent.git
cd Sale_Quote_Agent
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

Create a `.env` file in the root folder:

```
OPENAI_API_KEY=your_openai_api_key_here
```

### 5. Run the app

```bash
python main.py
```

The Gradio UI will open in your browser automatically.

---

## Project Structure

```
Sale_Quote_Agent/
├── main.py                  # Entry point — launches Gradio UI
├── requirements.txt         # Python dependencies
├── export_graph.py          # Exports LangGraph structure as image
├── data/
│   └── documents/           # Knowledge base: roster + pricing policy
├── src/
│   ├── agents/
│   │   └── sales_quote/     # LangGraph nodes and agent logic
│   ├── config/              # Settings and configuration
│   ├── core/                # LLM setup
│   └── rag/                 # RAG indexer and retriever (ChromaDB)
└── ui/
    └── app.py               # Gradio UI definition
```

---

## Features

- Accepts unstructured input in Vietnamese, English, or mixed language
- RAG-based search over delivery team roster and pricing policy documents
- Automatic discount calculation (duration, team size, capped at 25%)
- Policy validation with self-correction loop (up to 2 retries)
- Approval routing based on margin and discount thresholds
- Visual Gradio UI — no terminal interaction needed
- Graph export to verify agent structure

---

## Out of Scope (POC)

This is a Proof of Concept. The following are not included:

- Real-time HR/resource system sync
- CRM integration
- Contract or document generation
- Multi-turn negotiation
- Client-facing chatbot
