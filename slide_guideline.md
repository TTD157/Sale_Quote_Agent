# Slide Creation Guideline — Sale Quote Agent
> Demo presentation · 9 slides · Simple, concise, visual-first

---

## General Instructions for Gemini

- **Purpose**: This is a demo/POC presentation for a technical audience (developers, trainers, or assessors)
- **Tone**: Professional but approachable — not overly formal
- **Style**: Minimal text per slide, prefer visuals, diagrams, icons, and short bullet points
- **Language**: English
- **Bullets per slide**: Maximum 4–5 short bullets. No full sentences — use fragments
- **Font**: Clean sans-serif (e.g., Google Sans, Inter, or Roboto)
- **Color scheme**: Dark tech theme recommended (dark navy/black background, white text, accent in blue or teal) — or a clean light theme if preferred
- **Do NOT** include walls of text or long paragraphs on any slide

---

## Slide 1 — Title Slide

**Layout**: Centered, full-bleed background (dark or gradient)

**Content**:
- **Title**: Sale Quote Agent
- **Subtitle**: AI-powered Sales Support for IT Outsourcing Teams
- **Author**: [Your Name]
- **Date**: April 2026

**Design notes**:
- Add a subtle tech/AI visual in the background (circuit, graph nodes, or abstract data flow)
- Keep it clean — title and subtitle only, no bullet points

---

## Slide 2 — The Problem

**Layout**: Two-column or single column with icon bullets

**Heading**: The Problem

**Content**:
- Sales receives client needs through unstructured channels — meetings, emails, Slack
- Manual process: extract needs → find available staff → apply pricing → assemble quote
- Involves multiple people across sales and delivery teams
- Slow, error-prone, and hard to scale

**Design notes**:
- Use a simple pain-point icon (warning sign, clock, or broken chain) next to each bullet
- Optional: small "before" workflow diagram (linear boxes: Client → Sales → Delivery → Pricing → Quote)

---

## Slide 3 — The Solution

**Layout**: Single column or 3-icon row

**Heading**: The Solution

**Content**:
- AI agent that automates steps from raw input to policy-compliant quote
- Input: messy meeting notes, emails, or Slack messages (Vietnamese / English / mixed)
- Process: extract requirements → match team → configure package → validate pricing
- Output: structured, actionable quote ready for the sales team

**Design notes**:
- Use a simple 3-step visual: **Input → Agent → Output**
- Highlight "no more manual back-and-forth" as the core value

---

## Slide 4 — Agent Architecture

**Layout**: Full-width flow diagram, centered

**Heading**: Agent Architecture (LangGraph)

**Diagram** — render as a vertical or horizontal flow:

```
[START]
   ↓
Node 1: Extract Requirements       → LLM parses messy input → structured JSON
   ↓
Node 2: Check Delivery Capacity    → RAG search over team roster
   ↓
Node 3: Reason & Configure Package → LLM selects best-fit team + gap analysis
   ↓
Node 4: Apply Pricing & Policy     → RAG + LLM: pricing calc + policy validation
   ↓ (if invalid → back to Node 3, max 2 retries)
Node 5: Generate Output            → Final formatted summary for sales team
   ↓
[END]
```

**Design notes**:
- Use rounded rectangle boxes for each node, arrows between them
- Highlight the **retry loop** (Node 4 → Node 3) with a curved arrow and label "retry (max 2x)"
- Color-code: blue for LLM nodes, teal/green for RAG nodes

---

## Slide 5 — Tech Stack

**Layout**: Clean table or icon grid

**Heading**: Tech Stack

**Content**:

| Component        | Technology                     |
|------------------|-------------------------------|
| Agent Framework  | LangChain + LangGraph          |
| LLM              | OpenAI GPT-4o-mini             |
| Embeddings       | OpenAI text-embedding-3-small  |
| Vector Store     | ChromaDB (2 collections)       |
| UI               | Gradio                         |
| Language         | Python                         |

**Design notes**:
- Use logos/icons for each technology if possible (OpenAI, LangChain, Python, Gradio)
- Keep table minimal — no extra columns or descriptions

---

## Slide 6 — Live Demo

**Layout**: Full-screen screenshot or split: screenshot left, callouts right

**Heading**: Live Demo

**Content**:
- Show Gradio UI with a sample input (messy meeting notes)
- Show the structured output: team proposal + pricing table + policy status
- Callout labels pointing to key parts of the UI:
  - "Paste any unstructured input"
  - "Agent processes in real-time"
  - "Ready-to-use quote output"

**Design notes**:
- Use actual screenshot of the running Gradio app if available
- If doing a live demo, this slide is a placeholder — just show the heading and transition to the live app
- Add a subtle border or shadow around the screenshot

---

## Slide 7 — Limitations

**Layout**: Single column with icon bullets

**Heading**: Limitations

**Content**:
- Mock data only — no real-time HR or delivery system sync
- Stateless — no memory between sessions
- No CRM integration — output must be copied manually
- Retry loop capped at 2 — complex edge cases may be unhandled

**Design notes**:
- Use a subtle "caution" or "info" icon style — not alarming, just honest
- Keep it brief — this is an acknowledgment slide, not a problem slide

---

## Slide 8 — Future Development

**Layout**: Single column or 2-column (short-term / long-term)

**Heading**: Future Development

**Content**:
- Live HR/resource system integration for real-time availability
- CRM connector (Salesforce, HubSpot) to push quotes directly
- Multi-turn negotiation — agent iterates with salesperson interactively
- Client-facing chatbot interface
- Predictive bench planning based on upcoming project end dates

**Design notes**:
- Use a roadmap or timeline visual if space allows
- Optional split: **Near-term** (first 2 bullets) vs **Long-term** (last 3 bullets)
- Use forward-arrow or rocket icon to convey growth

---

## Slide 9 — Q&A / Closing

**Layout**: Centered, minimal

**Heading**: Thank You

**Content**:
- "Questions?" or "Open for discussion"
- GitHub repo link (optional): `github.com/TTD157/Sale_Quote_Agent`

**Design notes**:
- Match the style of Slide 1 (title slide) for visual bookending
- Keep it completely clean — no bullets, just the heading and a thank-you line

---

## Summary Table

| # | Slide Title            | Key Visual                  | Max Bullets |
|---|------------------------|-----------------------------|-------------|
| 1 | Title                  | Background graphic          | 0           |
| 2 | The Problem            | Icon bullets / mini diagram | 4           |
| 3 | The Solution           | 3-step flow                 | 4           |
| 4 | Agent Architecture     | LangGraph flow diagram      | 0 (diagram) |
| 5 | Tech Stack             | Table with icons            | 0 (table)   |
| 6 | Live Demo              | Gradio UI screenshot        | 3 callouts  |
| 7 | Limitations            | Icon bullets                | 4           |
| 8 | Future Development     | Roadmap / bullets           | 5           |
| 9 | Q&A / Closing          | Clean centered text         | 0           |
