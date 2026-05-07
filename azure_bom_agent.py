import os
import sys
import base64
import io
import time
from pathlib import Path
from typing import Type

import httpx
from PIL import Image as PILImage
from pydantic import BaseModel, Field
from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool

os.environ["GOOGLE_API_KEY"] = "AIzaSyB7IrpyY3fEFF9jgVsgJD_4U8t_JTWH-E4"

GEMINI_API_KEY = os.environ["GOOGLE_API_KEY"]
VISION_MODEL = "gemini-2.5-flash-lite"
GEMINI_VISION_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{VISION_MODEL}:generateContent?key={GEMINI_API_KEY}"
)
LLM_MODEL = "gemini/gemini-2.5-flash-lite"

MIME_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".pdf": "application/pdf",
}


# ---------------------------------------------------------------------------
# Vision Tool — calls Gemini REST API directly with the diagram image
# ---------------------------------------------------------------------------

class VisionToolInput(BaseModel):
    image_path: str = Field(description="Absolute or relative path to the architecture diagram image or PDF")


class GeminiVisionTool(BaseTool):
    name: str = "analyze_architecture_diagram"
    description: str = (
        "Analyzes an Azure solution architecture diagram image (PNG, JPG, PDF, etc.) "
        "and returns a detailed inventory of every Azure service, component, and resource "
        "visible in the diagram, along with quantities and connectivity."
    )
    args_schema: Type[BaseModel] = VisionToolInput

    def _run(self, image_path: str) -> str:
        path = Path(image_path)
        if not path.exists():
            return f"ERROR: File not found: {image_path}"

        suffix = path.suffix.lower()
        mime_type = MIME_TYPES.get(suffix, "image/png")

        # Resize to max 1024px on the longest side to keep payload small
        if suffix in (".png", ".jpg", ".jpeg", ".gif", ".webp"):
            img = PILImage.open(path)
            img.thumbnail((1024, 1024), PILImage.LANCZOS)
            buf = io.BytesIO()
            fmt = "PNG" if suffix == ".png" else "JPEG"
            img.save(buf, format=fmt)
            image_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
            mime_type = "image/png" if fmt == "PNG" else "image/jpeg"
        else:
            with open(path, "rb") as f:
                image_b64 = base64.b64encode(f.read()).decode("utf-8")

        prompt = (
            "You are an expert Azure solutions architect. Carefully examine this Azure "
            "solution architecture diagram and extract ALL Azure services and components.\n\n"
            "For each component provide:\n"
            "1. Service name (as labeled or as you recognise from the Azure icon)\n"
            "2. Azure service category (Compute / Networking / Storage / Security / "
            "   Database / Integration / AI+ML / Management / Identity / Other)\n"
            "3. Quantity / instance count (if shown or inferable)\n"
            "4. Tier or size if visible (e.g. Standard, Premium, S1, P2)\n"
            "5. Connections to other components\n\n"
            "Be thorough — list every resource, even those implied by the architecture pattern. "
            "Return the result as a numbered list."
        )

        payload = {
            "contents": [{
                "parts": [
                    {"inline_data": {"mime_type": mime_type, "data": image_b64}},
                    {"text": prompt},
                ]
            }]
        }

        for attempt in range(4):
            try:
                response = httpx.post(GEMINI_VISION_URL, json=payload, timeout=120)
                if response.status_code == 503 and attempt < 3:
                    wait = 2 ** attempt * 5
                    print(f"  [VisionTool] 503 overload, retrying in {wait}s (attempt {attempt+1}/4)...")
                    time.sleep(wait)
                    continue
                response.raise_for_status()
                data = response.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]
            except httpx.HTTPStatusError as e:
                if attempt < 3 and e.response.status_code in (429, 500, 503):
                    wait = 2 ** attempt * 5
                    print(f"  [VisionTool] HTTP {e.response.status_code}, retrying in {wait}s...")
                    time.sleep(wait)
                    continue
                return f"API error {e.response.status_code}: {e.response.text}"
            except Exception as e:
                return f"Vision tool error: {e}"
        return "Vision tool failed after 4 attempts."


# ---------------------------------------------------------------------------
# Agents
# ---------------------------------------------------------------------------

architecture_analyst = Agent(
    role="Azure Architecture Analyst",
    goal=(
        "Use the analyze_architecture_diagram tool to examine the provided architecture diagram "
        "and produce a complete, structured inventory of every Azure service and component present."
    ),
    backstory=(
        "You are a senior Azure solutions architect with 10+ years of experience reading and "
        "interpreting cloud architecture diagrams. You can identify any Azure service from its "
        "icon, label, or architectural context. You are meticulous and never miss a component."
    ),
    tools=[GeminiVisionTool()],
    allow_delegation=False,
    verbose=True,
    llm=LLM_MODEL,
)

resource_mapper = Agent(
    role="Azure Resource Specification Expert",
    goal=(
        "Map every identified Azure component to its official Azure resource name, "
        "resource provider type, recommended SKU/tier, quantity, and estimated monthly cost."
    ),
    backstory=(
        "You are an Azure pricing and resource configuration specialist. You know every Azure "
        "service's official name, ARM resource type, available SKUs, and public pricing. "
        "When specific details are not visible in a diagram you apply well-reasoned best-practice "
        "defaults and document your assumptions clearly."
    ),
    allow_delegation=False,
    verbose=True,
    llm=LLM_MODEL,
)

bom_compiler = Agent(
    role="Bill of Materials Compiler",
    goal=(
        "Compile all resource specifications into a professional, structured Azure "
        "Bill of Materials document formatted in markdown."
    ),
    backstory=(
        "You are a technical writer and Azure cost analyst who produces clear, actionable BOM "
        "documents used by procurement, engineering, and finance teams. Your documents are "
        "precise, well-formatted, and include all information needed to provision or quote "
        "the described architecture."
    ),
    allow_delegation=False,
    verbose=True,
    llm=LLM_MODEL,
)


# ---------------------------------------------------------------------------
# Crew builder
# ---------------------------------------------------------------------------

def build_crew(image_path: str) -> Crew:
    analyze_task = Task(
        description=(
            f"Analyze the Azure architecture diagram located at: {image_path}\n\n"
            "Use the analyze_architecture_diagram tool with that file path. "
            "From the tool's output, produce a clean structured list of all Azure "
            "components with their category, quantity, visible tier/size, and connections."
        ),
        expected_output=(
            "A numbered list of all Azure components found in the diagram. Each entry includes: "
            "service name, category, quantity, tier/size (if visible), and connected services."
        ),
        agent=architecture_analyst,
    )

    specify_task = Task(
        description=(
            "Using the component inventory from the previous task, map each item to its "
            "official Azure resource specification.\n\n"
            "For each resource provide:\n"
            "- Official Azure service name (e.g. 'Azure Application Gateway')\n"
            "- ARM resource type (e.g. 'Microsoft.Network/applicationGateways')\n"
            "- Recommended SKU / tier (apply best-practice defaults if not specified)\n"
            "- Quantity\n"
            "- Estimated monthly cost in USD (use Azure public pricing, note the region as "
            "  East US if not specified)\n"
            "- Brief justification for SKU choice\n\n"
            "List all assumptions you make."
        ),
        expected_output=(
            "A detailed specification list: one entry per resource with official name, "
            "ARM type, SKU, quantity, estimated monthly cost, and SKU justification. "
            "Followed by a numbered assumptions list."
        ),
        agent=resource_mapper,
        context=[analyze_task],
    )

    compile_task = Task(
        description=(
            "Compile the resource specifications into a final Azure Bill of Materials document.\n\n"
            "The document must contain:\n"
            "1. **Architecture Summary** — 2-3 sentences describing the overall solution pattern\n"
            "2. **Bill of Materials Table** with columns:\n"
            "   `#` | `Resource Name` | `Azure Service` | `ARM Resource Type` | "
            "`SKU / Tier` | `Qty` | `Unit Cost/mo (USD)` | `Total Cost/mo (USD)` | `Notes`\n"
            "3. **Cost Summary** — subtotals by category and a grand total\n"
            "4. **Assumptions & Caveats** — numbered list of all pricing assumptions\n\n"
            "Format the entire output as clean markdown."
        ),
        expected_output=(
            "A complete markdown Bill of Materials document with an architecture summary, "
            "full BOM table, cost summary with category subtotals and grand total, "
            "and a numbered assumptions list."
        ),
        agent=bom_compiler,
        context=[analyze_task, specify_task],
    )

    return Crew(
        agents=[architecture_analyst, resource_mapper, bom_compiler],
        tasks=[analyze_task, specify_task, compile_task],
        process=Process.sequential,
        verbose=True,
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print("Usage: python azure_bom_agent.py <path_to_architecture_diagram>")
        print("Supported formats: PNG, JPG, JPEG, GIF, WEBP, PDF")
        sys.exit(1)

    image_path = sys.argv[1]
    if not Path(image_path).exists():
        print(f"Error: file not found — {image_path}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("  Azure Bill of Materials Generator")
    print("=" * 60)
    print(f"  Input : {image_path}")
    print("=" * 60 + "\n")

    crew = build_crew(image_path)
    result = crew.kickoff()

    bom_text = str(result)

    output_path = Path(image_path).stem + "_bom.md"
    with open(output_path, "w") as f:
        f.write(bom_text)

    print("\n" + "=" * 60)
    print("  BILL OF MATERIALS")
    print("=" * 60)
    print(bom_text)
    print(f"\n  Saved to: {output_path}")


if __name__ == "__main__":
    main()
