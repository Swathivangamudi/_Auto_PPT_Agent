# Auto PPT Agent 🎯✨

A fully autonomous, agentic PowerPoint generator built natively on the **Model Context Protocol (MCP)** architecture. 

**Auto PPT Agent** doesn't just run a script to blindly dump text onto generic slides. It implements a true *Agentic Loop* using dual MCP servers to intelligently structure presentations, generate contextual textual content, fetch real-world imagery via Pexels, and compile polished, themed `.pptx` files.

---

## 🏗️ Architecture

The app satisfies complex AI agent architectures via the **Model Context Protocol (MCP)** over `stdio`. It runs three distinct components:

1. **The Core Agent (`agent_ppt.py`)** 
   - Uses HuggingFace's `Qwen/Qwen2.5-7B-Instruct` as the central LLM brain.
   - Operates a 5-Phase generative loop: *Plan → Initialize → Execute Loop → Save → Verify*.
2. **MCP Server 1: PPT Generator (`ppt_server.py`)**
   - Exposes three `@mcp.tool()` endpoints: `create_presentation`, `add_slide`, and `save_presentation`.
   - Embeds the Pexels API fetching logic natively so that the MCP communication schema remains 100% JSON-serializable.
   - Includes custom, rich visual themes with programmatic shape generation.
3. **MCP Server 2: FileSystem server (`file_system_server.py`)**
   - An independent MCP server utilized during the *Verification Phase* to inspect the local disk and prove that the `.pptx` file was generated correctly.

---

## 🎨 Features
*   **True Agentic Planning:** The LLM generates the entire structural JSON layout of the slideshow (Titles, slide types, matching visual search keywords) *before* it begins calling tools.
*   **Real Image Integration:** Connects out to Pexels inside the MCP Server to pull highly relevant landscape imagery onto content slides.
*   **Gorgeous Themes:** 5 custom styling profiles (`Dark Tech`, `Corporate Blue`, `Nature Green`, `Warm Sunset`, `Minimal White`) replacing standard stale themes.
*   **Intelligent Layouts:** Bullet points are programmatically anchored vertically ensuring perfect spacing regardless of content length.
*   **Streamlit UI:** A fully styled interface featuring a dark glassmorphic design that streams the exact MCP tooling procedure securely to the user in a terminal box.

---

## 🚀 Setup & Installation

### 1. Requirements
- Python 3.10+
- HuggingFace API key
- Pexels API key

### 2. Install Dependencies
Clone the repository, create a virtual environment, and install the requirements:

```bash
# Create and activate virtual environment
python -m venv .venv

# Windows
.\.venv\Scripts\Activate.ps1
# Mac/Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Variables
Create a `.env` file in the root directory and add your API keys:

```env
HUGGINGFACEHUB_API_TOKEN="your_huggingface_token_here"
PEXELS_API_KEY="your_pexels_key_here"
```


---

## 💻 Running the Application

To interact with the agent, simply run the Streamlit frontend:

```bash
streamlit run app.py
```

The application will be hosted locally at `http://localhost:8502`. From there, enter a topic prompt (e.g. *"Create a 5-slide presentation on the life cycle of a star for a 6th-grade class"*), pick a theme, and watch the agent negotiate with its MCP tools to build your presentation!

---
