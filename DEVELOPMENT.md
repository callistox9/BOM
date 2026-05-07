
# Azure Bill of Materials Generator — Development Log

## Goal

Build a multi-agent CrewAI system that accepts an Azure solution architecture diagram (image/PDF) and produces a structured Bill of Materials (BOM) listing every Azure resource, its SKU/tier, quantity, and estimated monthly cost.

---

## Environment Audit

**Working directory:** `/home/azureuser/crewAI`

**Existing file:** `agent.py` — a starter CrewAI party-planner demo using `gemini/gemini-2.5-flash` as the LLM.

**Virtual environment:** `venv/` (Python 3.12)

### Packages already installed (relevant)

| Package | Version | Purpose |
|---|---|---|
| crewai | 1.14.4 | Multi-agent orchestration framework |
| openai | 2.34.0 | OpenAI-compatible client |
| pillow | 12.2.0 | Image loading and processing |
| pdfplumber | 0.11.4 | PDF text/image extraction |
| httpx | 0.28.1 | Async HTTP client (used for REST calls) |
| chromadb | 1.1.1 | Vector store (available for memory) |

### Packages missing (discovered during audit)

| Package | Why needed | Resolution |
|---|---|---|
| `google-genai` | CrewAI routes `"gemini/..."` model strings to the native Google Gen AI SDK — without it, `LLM(model="gemini/gemini-2.5-flash")` raises `ImportError` | Installed via `pip install google-genai` |
| `litellm` | CrewAI's fallback LLM router — not needed once `google-genai` is present | Not installed, not needed |
| `crewai_files` | CrewAI's optional file-injection system for native multimodal task inputs | Not installed |

**Install command run:**
```bash
pip install google-genai
# Result: google-genai 1.75.0 installed
```

**Verification:**
```bash
python -c "
from crewai.llm import LLM
llm = LLM(model='gemini/gemini-2.5-flash')
print(llm.provider)   # gemini
print(type(llm).__name__)  # GeminiCompletion
"
```

---

## Architecture Decision: How to Pass Images to Agents

### Problem

CrewAI's built-in multimodal image support requires either:
- `crewai_files` (file injection via `task.input_files`) — **not installed**
- Native `google.genai` image parts injected into the task context — requires `crewai_files` to trigger

### Solution: Custom Vision Tool

Build a `GeminiVisionTool` (`crewai.tools.BaseTool`) that:
1. Accepts an image file path as input
2. Reads and base64-encodes the image using `pillow`
3. Calls the **Gemini REST API** directly via `httpx` with the image as an inline `inlineData` part
4. Returns the visual analysis as a plain text string

This keeps the vision call self-contained in a tool, and the rest of the CrewAI pipeline works with normal text messages. No extra packages required.

---

## Agent Design

### Pipeline: Sequential (3 agents → 3 tasks)

```
[Image File]
     │
     ▼
┌─────────────────────────────┐
│  Agent 1: Architecture      │  Uses GeminiVisionTool to identify
│  Analyst                    │  every Azure service in the diagram
└──────────────┬──────────────┘
               │ structured component list
               ▼
┌─────────────────────────────┐
│  Agent 2: Resource Mapper   │  Maps each component to official Azure
│                             │  resource type, SKU, tier, quantity
└──────────────┬──────────────┘
               │ resource specifications
               ▼
┌─────────────────────────────┐
│  Agent 3: BOM Compiler      │  Produces final markdown BOM table
│                             │  with cost estimates and totals
└─────────────────────────────┘
               │
               ▼
        <architecture>_bom.md
```

### Agent Responsibilities

| Agent | Role | Key Output |
|---|---|---|
| Architecture Analyst | Reads the diagram using vision, lists all Azure services, quantities, and connections | Structured component inventory |
| Resource Mapper | Maps each component to official Azure resource name, resource provider type, SKU/tier, and estimated unit cost | Fully specified resource list |
| BOM Compiler | Assembles everything into a professional markdown BOM document with a summary, table, totals, and assumptions | `<name>_bom.md` |

---

## File Structure

```
crewAI/
├── agent.py              # Original demo (unchanged)
├── azure_bom_agent.py    # Main entry point — run this
├── DEVELOPMENT.md        # This file
└── venv/
```

---

## Implementation Steps

### Step 1 — Environment audit and dependency fix
- Audited installed packages
- Identified missing `google-genai`
- Installed it, verified `LLM(model="gemini/gemini-2.5-flash")` resolves to `GeminiCompletion`

### Step 2 — Write `azure_bom_agent.py`

**File created:** `azure_bom_agent.py`

#### `GeminiVisionTool` (custom `BaseTool`)

Because `crewai_files` is not installed (the package that normally handles multimodal task inputs), images cannot be injected into tasks natively. Instead a custom tool was written:

- Accepts `image_path` as input (validated by a Pydantic `VisionToolInput` schema)
- Reads the file and base64-encodes it with Python's `base64` module
- Determines the MIME type from the file extension (`.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.pdf`)
- Posts the image as an `inline_data` part to the **Gemini REST API** (`gemini-2.5-flash`) using `httpx`
- Includes a detailed vision prompt asking for service name, category, quantity, tier, and connections
- Returns the plain-text analysis back to CrewAI as a tool result string

This keeps everything within the already-installed packages — no additional dependencies needed.

#### Agents

| Agent | Tools | LLM |
|---|---|---|
| `architecture_analyst` | `GeminiVisionTool` | `gemini/gemini-2.5-flash` |
| `resource_mapper` | *(none — text only)* | `gemini/gemini-2.5-flash` |
| `bom_compiler` | *(none — text only)* | `gemini/gemini-2.5-flash` |

#### Tasks

| Task | Agent | Context (inputs) |
|---|---|---|
| `analyze_task` | architecture_analyst | image file path |
| `specify_task` | resource_mapper | `analyze_task` output |
| `compile_task` | bom_compiler | `analyze_task` + `specify_task` outputs |

#### Output

- BOM printed to stdout
- Saved as `<input_filename>_bom.md` in the working directory

---

### Step 3 — Testing with a sample diagram

**Sample diagram created:** `create_sample_diagram.py` → `sample_azure_architecture.png`

A 1400×900 px diagram was generated using Pillow with 4 tiers:
- Internet / Edge Layer: Users, Azure DNS, Azure CDN, Application Gateway v2 + WAF, Azure Front Door, Public IP
- Application Layer: Load Balancer, VM Scale Set, AKS Cluster, Service Bus, App Service Plan, API Management
- Data Layer: SQL Database, Cosmos DB, Redis Cache, Blob Storage, Data Factory, Event Hubs
- Management & Security: Key Vault, Azure Monitor, Defender for Cloud, Azure Bastion, NSG x3, Azure Backup, AAD

#### Run 1 — FAILED: `gemini-2.5-flash` 503 overload

The REST vision call succeeded then the CrewAI LLM call itself hit 503 (model overloaded).
The tenacity retry in `GeminiCompletion` exhausted its attempts and raised `ServerError`.

#### Run 2 — FAILED: `gemini-2.0-flash` 429 quota

Switched model to `gemini-2.0-flash`. Got 429 RESOURCE_EXHAUSTED with `limit: 0` for the free tier —
this model has no free-tier quota on this API key.

#### Fix applied: probe available models, switch to `gemini-2.5-flash-lite`

Tested four models via direct REST calls:

| Model | Result |
|---|---|
| `gemini-1.5-flash` | 404 — not found on v1beta |
| `gemini-1.5-pro` | 404 — not found on v1beta |
| `gemini-2.5-pro` | 429 — quota exceeded |
| `gemini-2.5-flash-lite` | **200 OK** |

Confirmed `LLM(model="gemini/gemini-2.5-flash-lite")` resolves correctly in CrewAI.
Updated all model references in `azure_bom_agent.py` to `gemini-2.5-flash-lite`.

Also added image resizing in `GeminiVisionTool`: images are thumbnailed to 1024×1024 max
before base64 encoding to reduce REST payload size.

#### Run 3 — SUCCESS

All 3 tasks completed. Output saved to `sample_azure_architecture_bom.md`.

**BOM result summary:**
- 26 resources identified and costed
- Grand total estimated monthly cost: **$2,125.00 / month**
- Breakdown: Compute $730 · Networking $500 · Database $500 · Security $100 · Management $75 · Storage $35 · Integration $35

---

## Usage (once complete)

```bash
source venv/bin/activate
python azure_bom_agent.py path/to/architecture_diagram.png
```

Supported input formats: `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.pdf`

Output: `<filename>_bom.md` saved in the current directory, and printed to stdout.

---

## API Key

The Google Gemini API key is set via `os.environ["GOOGLE_API_KEY"]` in the script (same key used in `agent.py`).
