# ================================
# AUTO PPT AGENT — Assignment Version
# True Agentic Loop using MCP Protocol
# ================================
#
# Flow:
#   1. Connect to 2 MCP servers (ppt_server + file_system_server) via stdio
#   2. PLANNING PHASE  — LLM reads full prompt → generates slide plan as JSON
#   3. EXECUTION LOOP  — For each slide: LLM generates content → MCP add_slide call
#   4. SAVE PHASE      — MCP save_presentation call
#   5. VERIFY PHASE    — MCP list_files call (FileSystem Server) → confirm file exists
# ================================

import os
import sys
import json
import asyncio

from dotenv import load_dotenv
load_dotenv()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import TextContent
from huggingface_hub import InferenceClient

# ================================
# LLM CLIENT (HuggingFace)
# ================================
HF_TOKEN = os.getenv("HUGGINGFACEHUB_API_TOKEN")
if not HF_TOKEN:
    raise ValueError("HUGGINGFACEHUB_API_TOKEN missing from .env")

llm = InferenceClient(token=HF_TOKEN)
LLM_MODEL = "Qwen/Qwen2.5-7B-Instruct"

OUTPUT_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'output', 'final_presentation.pptx')
)

_SERVERS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'servers'))
PPT_SERVER_PATH = os.path.join(_SERVERS_DIR, 'ppt_server.py')
FS_SERVER_PATH  = os.path.join(_SERVERS_DIR, 'file_system_server.py')


# ================================
# LLM HELPER
# ================================
def _call_llm(prompt: str, max_tokens: int = 512, temperature: float = 0.4) -> str:
    """Call HuggingFace LLM and return text response."""
    try:
        response = llm.chat_completion(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message["content"].strip()
    except Exception as e:
        return f"ERROR: {str(e)}"


def _extract_json(text: str):
    """Extract the first JSON object or array from LLM output."""
    # Try to find JSON block
    for start_char, end_char in [('{', '}'), ('[', ']')]:
        start = text.find(start_char)
        end   = text.rfind(end_char) + 1
        if start != -1 and end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                pass
    return None


# ================================
# MCP HELPER
# ================================
async def _mcp_call(session: ClientSession, tool: str, args: dict, log) -> str:
    """Call an MCP tool and return the text result."""
    log(f"  ⚙️  [MCP → {tool}] args: {json.dumps(args, default=str)[:120]}")
    try:
        result = await session.call_tool(tool, args)
        if result.content:
            content = result.content[0]
            if isinstance(content, TextContent):
                text = content.text
            else:
                text = str(content)
        else:
            text = "(no response)"
        log(f"  ✅ [MCP ← {tool}] {text[:100]}")
        return text
    except Exception as e:
        msg = f"❌ MCP error on {tool}: {str(e)}"
        log(msg)
        return msg


# ================================
# PHASE 1: PLANNING
# ================================
def _plan_slides(user_request: str, num_slides: int, tone: str, log) -> list:
    """
    Ask the LLM to generate an explicit slide plan BEFORE any slide is created.
    Returns a list of slide dicts: [{title, type, image_keyword}, ...]
    """
    log("🧠 [PLANNING PHASE] Asking LLM to plan presentation structure...")

    prompt = f"""You are an expert presentation planner.

User request: "{user_request}"
Presentation tone: {tone}
Number of slides: {num_slides} (including title and conclusion)

Plan the full presentation structure. Output ONLY a valid JSON array — no markdown, no explanation:
[
  {{"title": "slide title", "type": "title", "image_keyword": "pexels search term"}},
  {{"title": "slide title", "type": "content", "image_keyword": "pexels search term"}},
  ...
  {{"title": "Thank You", "type": "conclusion", "image_keyword": ""}}
]

Rules:
- First slide must have type "title"
- Last slide must have type "conclusion"
- Middle slides must have type "content"  
- image_keyword must be 2-4 words for Pexels image search
- Adapt the slide titles to perfectly suit the user request
- If the request is vague (e.g. "make a good ppt"), pick a relevant professional topic"""

    raw = _call_llm(prompt, max_tokens=600, temperature=0.3)
    log(f"  📋 LLM plan response:\n{raw[:500]}")

    plan = _extract_json(raw)

    if not isinstance(plan, list) or len(plan) == 0:
        log("  ⚠️  JSON parse failed — using default plan")
        # Graceful fallback
        topic = user_request[:60] if user_request else "Presentation"
        plan = [
            {"title": topic, "type": "title", "image_keyword": topic[:30]},
            {"title": "Introduction", "type": "content", "image_keyword": topic[:20]},
            {"title": "Key Concepts", "type": "content", "image_keyword": topic[:20]},
            {"title": "Applications", "type": "content", "image_keyword": topic[:20]},
            {"title": "Conclusion", "type": "conclusion", "image_keyword": ""},
        ]

    log(f"  ✅ Plan ready: {len(plan)} slides — {[s['title'] for s in plan]}")
    return plan


# ================================
# PHASE 2: CONTENT GENERATION (per slide)
# ================================
def _generate_content(user_request: str, slide: dict, tone: str, log) -> dict:
    """Ask LLM to generate bullet content for one slide."""
    if slide["type"] in ("title", "conclusion"):
        return slide  # no bullets needed

    log(f"  💬 Generating content for: '{slide['title']}'")

    prompt = f"""Create detailed bullet points for this presentation slide.

Presentation topic/request: "{user_request}"
Slide title: "{slide['title']}"
Tone: {tone}

Output ONLY valid JSON — no markdown:
{{
  "bullets": [
    "First clear bullet point sentence",
    "Second bullet point",
    "Third bullet point",
    "Fourth bullet point"
  ],
  "image_keyword": "specific 2-4 word pexels search term"
}}

Rules:
- 3 to 5 bullet points
- Each bullet: one clear, informative sentence (not too long)
- image_keyword must be visual and specific to this slide's topic"""

    raw = _call_llm(prompt, max_tokens=350, temperature=0.4)
    data = _extract_json(raw)

    if not data or "bullets" not in data:
        log(f"  ⚠️  JSON parse failed for '{slide['title']}' — using fallback")
        data = {
            "bullets": [
                f"Key insight about {slide['title']}",
                "Important supporting detail",
                "Real-world application or example",
                "Summary and significance",
            ],
            "image_keyword": slide.get("image_keyword", user_request[:20]),
        }

    return {**slide, **data}


# ================================
# ASYNC AGENT CORE
# ================================
async def _run_async(user_request: str, theme: str, num_slides: int,
                     tone: str, log):
    """
    The actual async agentic loop connecting to 2 MCP servers.
    """
    ppt_params = StdioServerParameters(
        command=sys.executable,
        args=[PPT_SERVER_PATH],
        env=dict(os.environ),
    )
    fs_params = StdioServerParameters(
        command=sys.executable,
        args=[FS_SERVER_PATH],
        env=dict(os.environ),
    )

    log("🔌 Connecting to MCP Server 1: ppt_server...")
    async with stdio_client(ppt_params) as (ppt_r, ppt_w):
        async with ClientSession(ppt_r, ppt_w) as ppt:
            await ppt.initialize()

            # Log available tools from MCP Server 1
            tools1 = await ppt.list_tools()
            tool_names1 = [t.name for t in tools1.tools]
            log(f"  📦 PPT Server tools: {tool_names1}")

            log("🔌 Connecting to MCP Server 2: file_system_server...")
            async with stdio_client(fs_params) as (fs_r, fs_w):
                async with ClientSession(fs_r, fs_w) as fs:
                    await fs.initialize()

                    tools2 = await fs.list_tools()
                    tool_names2 = [t.name for t in tools2.tools]
                    log(f"  📦 FileSystem Server tools: {tool_names2}")

                    # ── PHASE 1: PLANNING ──────────────────────
                    plan = _plan_slides(user_request, num_slides, tone, log)

                    # ── PHASE 2: CREATE PRESENTATION ───────────
                    log(f"\n🎨 [MCP CALL] Initializing presentation (theme: {theme})...")
                    await _mcp_call(ppt, "create_presentation",
                                    {"theme_name": theme}, log)

                    # ── PHASE 3: EXECUTION LOOP ─────────────────
                    log(f"\n🔄 [EXECUTION LOOP] Building {len(plan)} slides...\n")
                    for i, slide in enumerate(plan):
                        log(f"── Slide {i+1}/{len(plan)}: {slide['title']} ({slide['type']}) ──")

                        # Generate content with LLM
                        enriched = _generate_content(user_request, slide, tone, log)

                        # Build MCP tool arguments
                        if enriched["type"] == "title":
                            args = {
                                "title":         enriched["title"],
                                "content":       f"A {tone} presentation",
                                "image_keyword": enriched.get("image_keyword", ""),
                                "slide_type":    "title",
                            }
                        elif enriched["type"] == "conclusion":
                            args = {
                                "title":         enriched["title"],
                                "content":       "",
                                "image_keyword": "",
                                "slide_type":    "conclusion",
                            }
                        else:
                            bullets = enriched.get("bullets", [])
                            args = {
                                "title":         enriched["title"],
                                "content":       "\n".join(bullets),
                                "image_keyword": enriched.get("image_keyword", ""),
                                "slide_type":    "content",
                            }

                        # ── MCP TOOL CALL: add_slide ──
                        await _mcp_call(ppt, "add_slide", args, log)

                    # ── PHASE 4: SAVE ───────────────────────────
                    log(f"\n💾 [MCP CALL] Saving presentation...")
                    save_result = await _mcp_call(ppt, "save_presentation",
                                                  {"file_path": OUTPUT_PATH}, log)

                    # ── PHASE 5: VERIFY (FileSystem MCP Server) ─
                    log(f"\n🔍 [MCP CALL — Server 2] Verifying output file...")
                    output_dir = os.path.dirname(OUTPUT_PATH)
                    verify_result = await _mcp_call(fs, "list_files",
                                                    {"folder_path": output_dir}, log)
                    log(f"  📂 Files in output/: {verify_result}")

                    if "final_presentation.pptx" in verify_result:
                        log(f"\n✅ AGENT COMPLETE — file confirmed at: {OUTPUT_PATH}")
                        return OUTPUT_PATH
                    else:
                        log(f"\n⚠️  Warning: file not found in directory listing")
                        return OUTPUT_PATH


# ================================
# PUBLIC SYNC WRAPPER (for Streamlit)
# ================================
def run_agent(user_request: str, theme: str = "Dark Tech",
              num_slides: int = 5, tone: str = "Professional",
              progress_callback=None):
    """
    Synchronous wrapper around the async agent.
    Runs in a fresh thread with its own event loop
    (avoids Streamlit event loop conflicts).
    """
    logs = []

    def log(msg: str):
        print(msg)
        logs.append(msg)
        if progress_callback:
            # Estimate progress from log count
            pct = min(0.95, len(logs) / (num_slides * 6 + 10))
            progress_callback(pct, msg)

    import concurrent.futures

    def _run():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                _run_async(user_request, theme, num_slides, tone, log)
            )
        finally:
            loop.close()

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
        future = ex.submit(_run)
        result = future.result(timeout=300)  # 5-minute max

    if progress_callback:
        progress_callback(1.0, "✅ Done!")
    return result


# ================================
# CLI TEST
# ================================
if __name__ == "__main__":
    req   = input("Enter your presentation request: ").strip() \
            or "Create a 5-slide presentation on the life cycle of a star for a 6th-grade class"
    theme = input("Theme (Dark Tech / Corporate Blue / Nature Green / Warm Sunset / Minimal White): ").strip() \
            or "Dark Tech"
    run_agent(req, theme=theme, num_slides=5, tone="Professional")