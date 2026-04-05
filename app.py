import streamlit as st
import os

from agent.agent_ppt import run_agent

# ================================
# PAGE CONFIG
# ================================
st.set_page_config(
    page_title="Auto PPT Agent ✨",
    page_icon="🎯",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ================================
# CUSTOM CSS (Dark Glassmorphism Theme)
# ================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
*, *::before, *::after { font-family: 'Inter', sans-serif !important; }

.stApp {
    background: linear-gradient(135deg, #1a0f0d 0%, #28140a 40%, #2a0c0c 100%);
    min-height: 100vh;
}
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 2rem !important; padding-bottom: 2rem !important; }

/* Hero */
.hero { text-align: center; padding: 2.5rem 1rem 1.5rem; }
.hero-badge {
    display: inline-block;
    background: rgba(255, 138, 0, 0.15);
    border: 1px solid rgba(255, 138, 0, 0.35);
    color: #ffad66; font-size: 0.78rem; font-weight: 600;
    letter-spacing: 0.12em; text-transform: uppercase;
    padding: 6px 18px; border-radius: 99px; margin-bottom: 1.2rem;
}
.hero h1 {
    font-size: 3.2rem; font-weight: 800;
    background: linear-gradient(90deg, #ff8a00 0%, #ff5e00 45%, #e52e71 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin: 0 0 0.6rem; line-height: 1.1;
}
.hero p { color: #8899bb; font-size: 1.05rem; }

hr { border-color: rgba(255,255,255,0.07) !important; margin: 1.2rem 0 !important; }

/* Labels */
.stTextInput label, .stSelectbox label, .stTextArea label {
    color: #c0cce8 !important; font-size: 0.88rem !important;
    font-weight: 600 !important; letter-spacing: 0.03em !important;
}

/* Text input */
.stTextInput > div > div > input, .stTextArea > div > div > textarea {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.14) !important;
    border-radius: 12px !important; color: #e8eeff !important;
    font-size: 1rem !important;
}
.stTextInput > div > div > input:focus {
    border-color: #ff8a00 !important;
    box-shadow: 0 0 0 3px rgba(255, 138, 0, 0.2) !important;
}

/* Selectbox */
.stSelectbox > div > div {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.14) !important;
    border-radius: 12px !important; color: #e8eeff !important;
}

/* Generate button */
.stButton > button {
    background: linear-gradient(135deg, #ff8a00 0%, #e52e71 100%) !important;
    color: #fff !important; border: none !important;
    border-radius: 14px !important; padding: 0.85rem 2rem !important;
    font-size: 1.05rem !important; font-weight: 700 !important;
    width: 100% !important; letter-spacing: 0.02em !important;
    transition: transform 0.2s, box-shadow 0.2s !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 10px 28px rgba(255, 138, 0, 0.45) !important;
}

/* Download button */
.stDownloadButton > button {
    background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%) !important;
    color: #fff !important; border: none !important;
    border-radius: 14px !important; padding: 0.85rem 2rem !important;
    font-size: 1.05rem !important; font-weight: 700 !important;
    width: 100% !important;
}

/* Log box (if needed) */
.log-box {
    background: rgba(0,0,0,0.4);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 12px;
    padding: 1rem 1.2rem;
    font-family: 'Courier New', monospace !important;
    font-size: 0.78rem;
    color: #7aecb4;
    max-height: 320px;
    overflow-y: auto;
    white-space: pre-wrap;
    margin: 1rem 0;
}

/* Theme badge */
.theme-card {
    display: flex; align-items: center; gap: 10px;
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 12px; padding: 0.7rem 1rem; margin: 0.5rem 0 1rem;
}
.theme-dot { width: 14px; height: 14px; border-radius: 50%; flex-shrink: 0; }
.theme-name { color: #c0cce8; font-size: 0.88rem; font-weight: 500; }

/* Result box */
.result-box {
    background: rgba(255, 138, 0, 0.08);
    border: 1px solid rgba(255, 138, 0, 0.25);
    border-radius: 14px; padding: 1rem 1.3rem;
    margin: 1rem 0; text-align: center;
    color: #ffd5b5; font-size: 0.92rem;
}
.result-box strong { color: #fff1e6; }
.footer { text-align: center; color: #3a4460; font-size: 0.82rem; padding: 1.5rem 0 0.5rem; }
</style>
""", unsafe_allow_html=True)

# ================================
# HERO
# ================================
st.markdown("""
<div class="hero">
    <div class="hero-badge">✦ AI Agents &amp; MCP Architecture</div>
    <h1>Auto PPT Agent</h1>
    <p>Agentic loop · MCP tool calling · Real images · Themed slides</p>
</div>
""", unsafe_allow_html=True)
st.markdown("---")

# ================================
# THEME METADATA
# ================================
THEME_META = {
    "Dark Tech":      {"color": "#e94560", "emoji": "🌑"},
    "Corporate Blue": {"color": "#0088ff", "emoji": "🏢"},
    "Nature Green":   {"color": "#52b788", "emoji": "🌿"},
    "Warm Sunset":    {"color": "#ff6b35", "emoji": "🌅"},
    "Minimal White":  {"color": "#4a90e2", "emoji": "⬜"},
}

# ================================
# FORM
# ================================
user_request = st.text_area(
    "📝 Presentation Request",
    placeholder='E.g. "Create a 5-slide presentation on the life cycle of a star for a 6th-grade class"',
    height=90,
)

col_count, col_theme, col_tone = st.columns(3)
with col_count:
    num_slides = st.selectbox("📊 Slides", [5, 8, 10], index=0)
with col_theme:
    theme = st.selectbox("🎨 Theme", list(THEME_META.keys()), index=0)
with col_tone:
    tone = st.selectbox("🗣️ Tone", ["Professional", "Creative", "Academic", "Simple"], index=0)

# Theme preview
if theme:
    meta  = THEME_META[theme]
    color = meta["color"]
    emoji = meta["emoji"]
    st.markdown(f"""
    <div class="theme-card">
        <div class="theme-dot" style="background:{color}; box-shadow:0 0 8px {color}88;"></div>
        <span class="theme-name">{emoji} &nbsp;<strong style="color:#e0e8ff;">{theme}</strong>
        &nbsp;·&nbsp; {num_slides} slides &nbsp;·&nbsp; {tone} tone</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("")

# ================================
# GENERATE
# ================================
if st.button("🚀 Generate Presentation", use_container_width=True):
    if not user_request.strip():
        st.warning("⚠️ Please describe your presentation topic.")
    else:
        with st.spinner("🤖 Agent is thinking and building the presentation... (Check terminal for full MCP trace)"):
            try:
                # Run the agent (it will block but Streamlit spinner will show)
                path = run_agent(
                    user_request=user_request.strip(),
                    theme=theme,
                    num_slides=num_slides,
                    tone=tone,
                    progress_callback=None
                )
                
                if path and os.path.exists(path):
                    st.success("🎉 **Presentation generated successfully!**")
                    
                    meta  = THEME_META[theme]
                    color = meta["color"]
                    st.markdown(f"""
                    <div class="result-box">
                        <strong>{user_request[:60]}...</strong><br>
                        {num_slides + 2} slides &nbsp;·&nbsp;
                        <span style="color:{color};">■</span> {theme} theme &nbsp;·&nbsp;
                        {tone} tone
                    </div>
                    """, unsafe_allow_html=True)
                    
                    with open(path, "rb") as f:
                        safe_name = "".join(c if c.isalnum() or c in " _-" else "_"
                                            for c in user_request[:40]).strip()
                        st.download_button(
                            label="📥 Download Presentation (.pptx)",
                            data=f,
                            file_name=f"{safe_name}_presentation.pptx",
                            mime=(
                                "application/vnd.openxmlformats-"
                                "officedocument.presentationml.presentation"
                            ),
                            use_container_width=True,
                        )
                else:
                    st.error("❌ File not created. Check the terminal above for errors.")
                    
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

# ================================
# FOOTER
# ================================
st.markdown("---")
st.markdown("""
<div class="footer">
    ✨ Powered by <strong>HuggingFace Qwen</strong> · <strong>Pexels API</strong>
    · <strong>MCP Protocol</strong> (2 servers) &nbsp;|&nbsp; Auto PPT Agent
</div>
""", unsafe_allow_html=True)