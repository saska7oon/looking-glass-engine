"""
Looking Glass Engine — Streamlit GUI.

A web-based consciousness interface that runs in the browser.
Connects to the same engine backend as the CLI but provides
a visual, interactive experience.

Run with: streamlit run ui/app.py
"""

import streamlit as st
import os
import logging
from datetime import datetime
from typing import Optional

from looking_glass.config import config
from looking_glass.engine import LookingGlassEngine
from looking_glass.renderer import FieldRenderer

logger = logging.getLogger(__name__)

# Page config
st.set_page_config(
    page_title="Looking Glass Engine",
    page_icon="🪞",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Import field module for region definitions
from looking_glass.field import ConsciousnessField

# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        border-bottom: 2px solid #4a90d9;
        margin-bottom: 2rem;
    }
    .main-header h1 {
        color: #4a90d9;
        font-size: 2.5rem;
        margin: 0;
    }
    .main-header p {
        color: #666;
        font-size: 1.1rem;
        margin: 0.5rem 0 0 0;
    }
    .state-card {
        background: #f0f4f8;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 4px solid #4a90d9;
    }
    .state-card h3 {
        margin: 0 0 1rem 0;
        color: #333;
    }
    .state-metric {
        display: inline-block;
        margin: 0.5rem 1rem 0.5rem 0;
        padding: 0.5rem 1rem;
        background: white;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .state-metric .label {
        font-size: 0.8rem;
        color: #888;
        text-transform: uppercase;
    }
    .state-metric .value {
        font-size: 1.5rem;
        font-weight: bold;
        color: #4a90d9;
    }
    .response-box {
        background: #fafafa;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid #e0e0e0;
        line-height: 1.8;
    }
    .region-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: bold;
        color: white;
    }
    .region-surface { background: #95a5a6; }
    .region-deep { background: #2c3e50; }
    .region-flow { background: #27ae60; }
    .region-anxiety { background: #e74c3c; }
    .region-open { background: #3498db; }
    .region-shadow { background: #8e44ad; }
    .region-transcendent { background: #f39c12; }
    .region-unmapped { background: #bdc3c7; color: #333; }
    .resonance-bar {
        height: 8px;
        border-radius: 4px;
        background: #ecf0f1;
        margin: 0.25rem 0;
        overflow: hidden;
    }
    .resonance-fill {
        height: 100%;
        border-radius: 4px;
        background: #4a90d9;
        transition: width 0.5s ease;
    }
    .command-hint {
        color: #999;
        font-size: 0.85rem;
        font-style: italic;
    }
    .aether-cast {
        background: linear-gradient(135deg, #1a1a3a, #2c1a3a);
        color: #d9c8ff;
        border: 1px solid #4a3a7a;
        border-radius: 8px;
        padding: 0.5rem 0.9rem;
        margin: 0.5rem 0 1rem 0;
        font-size: 0.95rem;
    }
    .aether-reveal {
        margin-left: 0.5rem;
        cursor: help;
        opacity: 0.7;
    }
    .takeaway-box {
        background: #f4f0ff;
        border-left: 4px solid #8e44ad;
        border-radius: 8px;
        padding: 0.8rem 1.1rem;
        margin: 0.5rem 0;
        color: #4a3760;
    }
</style>
""", unsafe_allow_html=True)


def get_region_css_class(region_name: str) -> str:
    """Map region names to CSS classes for color coding."""
    mapping = {
        "Surface Mind": "region-surface",
        "Deep Stillness": "region-deep",
        "Activated Flow": "region-flow",
        "Anxiety Spiral": "region-anxiety",
        "Open Receptivity": "region-open",
        "Shadow Depth": "region-shadow",
        "Transcendent Peak": "region-transcendent",
    }
    return mapping.get(region_name, "region-unmapped")


def _list_users() -> list[str]:
    """Lightweight list of user accounts (used before the engine is built)."""
    try:
        from looking_glass.tracker import SynchronicityTracker
        t = SynchronicityTracker()
        users = t.get_users()
        t.close()
        return users
    except Exception:
        return []


def render_field_map_html(field, state: Optional[dict] = None, response: str = "", region: str = "") -> str:
    """Render the consciousness field as an HTML canvas visualization."""
    import math

    # Field dimensions
    width, height = 600, 400
    margin = 40
    plot_w = width - 2 * margin
    plot_h = height - 2 * margin

    # Scale factors
    x_scale = plot_w / (config.field_x_range * 2)
    y_scale = plot_h / (config.field_y_range * 2)

    def to_screen(x, y):
        sx = margin + x * x_scale + plot_w / 2
        sy = margin + plot_h / 2 - y * y_scale
        return sx, sy

    # Build SVG
    svg_parts = []
    svg_parts.append(f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
                     f'style="background: #0a0a1a; border-radius: 10px; border: 1px solid #333;">')

    # Grid lines
    for i in range(-5, 6):
        x1, y1 = to_screen(i * 2, -config.field_y_range)
        x2, y2 = to_screen(i * 2, config.field_y_range)
        svg_parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                        f'stroke="#1a1a3a" stroke-width="1"/>')
        x1, y1 = to_screen(-config.field_x_range, i * 2)
        x2, y2 = to_screen(config.field_x_range, i * 2)
        svg_parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                        f'stroke="#1a1a3a" stroke-width="1"/>')

    # Axes
    ox, oy = to_screen(0, 0)
    svg_parts.append(f'<line x1="{margin}" y1="{oy}" x2="{width - margin}" y2="{oy}" '
                    f'stroke="#333" stroke-width="1"/>')
    svg_parts.append(f'<line x1="{ox}" y1="{margin}" x2="{ox}" y2="{height - margin}" '
                    f'stroke="#333" stroke-width="1"/>')

    # Axis labels
    svg_parts.append(f'<text x="{width/2}" y="{height - 5}" fill="#666" font-size="10" text-anchor="middle">+X = Activated</text>')
    svg_parts.append(f'<text x="{width/2}" y="{height - 20}" fill="#666" font-size="10" text-anchor="middle">-X = Calm</text>')
    svg_parts.append(f'<text x="{5}" y="{height/2}" fill="#666" font-size="10" text-anchor="middle" '
                    f'transform="rotate(-90, 5, {height/2})">+Y = Deep</text>')
    svg_parts.append(f'<text x="{5}" y="{height/2 + 15}" fill="#666" font-size="10" text-anchor="middle" '
                    f'transform="rotate(-90, 5, {height/2 + 15})">-Y = Surface</text>')

    # Region circles + labels
    region_colors = {
        "Surface Mind": "#95a5a6",
        "Deep Stillness": "#2c3e50",
        "Activated Flow": "#27ae60",
        "Anxiety Spiral": "#e74c3c",
        "Open Receptivity": "#3498db",
        "Shadow Depth": "#8e44ad",
        "Transcendent Peak": "#f39c12",
    }
    for r in ConsciousnessField.REGIONS:
        rx, ry = to_screen(r.center.x, r.center.y)
        color = region_colors.get(r.name, "#bdc3c7")
        # Radius in screen units from field coords (approximate on X axis)
        r_px = r.radius * x_scale
        svg_parts.append(
            f'<circle cx="{rx}" cy="{ry}" r="{r_px}" fill="{color}" '
            f'fill-opacity="0.10" stroke="{color}" stroke-opacity="0.4" '
            f'stroke-dasharray="4 2"/>'
        )
        svg_parts.append(
            f'<text x="{rx}" y="{ry}" fill="{color}" font-size="9" '
            f'text-anchor="middle" font-weight="bold">{r.name}</text>'
        )

    # Plot field history as a trail
    if field and hasattr(field, 'history'):
        trail = field.history[-30:]
        for i, point in enumerate(trail):
            sx, sy = to_screen(point.x, point.y)
            alpha = 0.3 + 0.7 * (i / len(trail)) if trail else 0.5
            size = 2 + 3 * (i / len(trail)) if trail else 3
            svg_parts.append(f'<circle cx="{sx}" cy="{sy}" r="{size}" '
                           f'fill="#4a90d9" opacity="{alpha}"/>')

    # Plot current position
    if field and field.current:
        cx, cy = to_screen(field.current.x, field.current.y)
        # Glow effect
        svg_parts.append(f'<circle cx="{cx}" cy="{cy}" r="15" fill="#4a90d9" opacity="0.2"/>')
        svg_parts.append(f'<circle cx="{cx}" cy="{cy}" r="8" fill="#4a90d9" opacity="0.6"/>')
        svg_parts.append(f'<circle cx="{cx}" cy="{cy}" r="4" fill="#ffffff"/>')

        # State vector arrow
        if state:
            ax, ay = to_screen(
                field.current.x + state.arousal * 0.5,
                field.current.y + state.depth * 0.5
            )
            svg_parts.append(f'<line x1="{cx}" y1="{cy}" x2="{ax}" y2="{ay}" '
                           f'stroke="#e74c3c" stroke-width="2" marker-end="url(#arrowhead)"/>')

    # Arrowhead marker
    svg_parts.append('<defs><marker id="arrowhead" markerWidth="10" markerHeight="7" '
                    f'refX="10" refY="3.5" orient="auto"><polygon points="0 0, 10 3.5, 0 7" '
                    f'fill="#e74c3c"/></marker></defs>')

    svg_parts.append('</svg>')
    return "\n".join(svg_parts)


def main():
    """Main Streamlit app."""
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🪞 Looking Glass Engine</h1>
        <p>Software-only consciousness interface — explore your inner field</p>
    </div>
    """, unsafe_allow_html=True)

    # Whole-app help — one place that explains what this is and how it works
    with st.expander("❓ What is this? How does it work?", expanded=False):
        st.markdown("""
**In one sentence:** you ask a question, the app reads your emotional/mental state
from *how you write*, plots that state on a 3D "consciousness field", and then asks
an AI to answer you *in light of that state* — so the response is shaped by where
your awareness is, not just what you asked.

**The idea behind it (no mysticism, just a useful lens):** the way we phrase a
question carries real information — anxious questions sound urgent, curious ones
sound open, heavy ones sound deep. The app captures that signal and uses it to
make the AI's answer feel more attuned to you.

**What happens when you press Send (the pipeline):**
1. **The oracle is cast** — each session, a personality/voice is drawn from the
   aether by genuine chance (a seed from time + your state as a bias). It stays
   constant for the whole session, then re-casts next time. You can reveal how
   it was chosen.
2. **Read your state** — your question text is scanned for
   emotional tone, question-framing, urgency, and contemplative words. That produces
   three honest *tendencies* (low-moderate confidence): **Arousal** (calm ↔
   activated), **Depth** (surface ↔ deep), and **Self-disclosure** (guarded ↔
   receptive). You can correct any of them.
3. **Plot it on the field** — those three numbers place a glowing point on a
   3D map with named archetypal "regions" (e.g. *Open Receptivity*, *Anxiety
   Spiral*). The app tells you which region you're nearest.
4. **Ask the oracle** — your question *plus* your state readout is sent, in
   this session's voice, to the backend you picked (your **local Ollama** model,
   or **cloud OpenRouter**).
5. **Show resonance** — bars show which regions your state most resembles.
6. **Door to carry** — every reply ends in a takeaway: a reframe, a micro-step,
   a question to hold, or a split of what can change vs. what to accept.
7. **Remember it** — every session is saved to a local database, scoped to
   **your name** (Session History), so the oracle can name patterns back to you
   over time (Pattern Analysis). Different users get separate histories.

**What it's NOT:** it cannot read your mind, predict the future, or channel
anything. The oracle voice is a lot-cast persona — you can always reveal how it
was generated. It's a structured, honest tool for self-reflection, not magic or
therapy.

**Quick start:** pick your name, leave the backend on **ollama**, keep the
default host/model, type a question in the box, press **Send 🔮**. That's it.
        """, unsafe_allow_html=True)

    # Sidebar configuration
    with st.sidebar:
        st.header("Configuration")
        st.caption("Hover any control to learn what it does.")

        # Backend selection
        backend = st.selectbox(
            "AI Backend",
            ["ollama", "openrouter"],
            index=0 if config.backend == "ollama" else 1,
            help=("Which engine powers the field's responses. "
                  "'ollama' runs a local model on your own machine (free, private, "
                  "works fully offline). 'openrouter' sends your question to a "
                  "cloud model through OpenRouter (needs an API key, costs per use). "
                  "Switch any time — changes take effect immediately."),
        )

        # Ollama settings (shown when Ollama is selected)
        if backend == "ollama":
            st.caption("Ollama is a local AI model server. These settings point "
                       "the app at the running Ollama container on your machine.")
            ollama_host = st.text_input(
                "Ollama Host",
                value=config.ollama_host,
                help=("Hostname or IP address where Ollama is running. "
                      "On this setup it is 'ollama' (the container name). "
                      "Use 'localhost' or '127.0.0.1' if Ollama runs directly "
                      "on this machine."),
            )
            ollama_port = int(st.number_input(
                "Ollama Port",
                value=float(config.ollama_port),
                min_value=1024.0,
                max_value=65535.0,
                step=1.0,
                help=("The network port Ollama listens on. The default is 11434. "
                      "Leave this as-is unless you changed Ollama's port."),
            ))
            ollama_model = st.text_input(
                "Ollama Model",
                value=config.ollama_model,
                help=("The name of the model to use inside your Ollama container, "
                      "for example 'ornith:9b'. You can see available models by "
                      "running 'ollama list' in the container."),
            )
            # Keep openrouter values from config (not shown)
            openrouter_api_key = config.openrouter_api_key
            openrouter_model = config.openrouter_model
        else:
            # OpenRouter settings (shown when OpenRouter is selected)
            st.caption("OpenRouter is a cloud AI gateway. The field sends your "
                       "question to a cloud model; a small per-use cost applies.")
            openrouter_api_key = st.text_input(
                "OpenRouter API Key",
                value=config.openrouter_api_key,
                type="password",
                help=("Your secret OpenRouter key (sk-or-v1-...). Get one free at "
                      "openrouter.ai/keys. This is stored in your .env file and "
                      "only ever sent to OpenRouter — never shared. You can also "
                      "set it as the OPENROUTER_API_KEY environment variable."),
            )
            openrouter_model = st.text_input(
                "OpenRouter Model",
                value=config.openrouter_model,
                help=("Which cloud model to use, e.g. 'inclusionai/ling-3.0-flash:free'. "
                      "Pick a free/:free model to avoid charges, or any model ID "
                      "listed at openrouter.ai/models."),
            )
            if st.button(
                "💾 Save key to .env",
                help=("Reveals a field to securely save the OpenRouter API key to "
                      "your .env file (permissions 0600, owner-only) so you don't "
                      "have to re-enter it every session. Your .env is git-ignored "
                      "and never committed or shared. If a key is already stored, "
                      "it is overwritten."),
            ):
                if not openrouter_api_key.strip():
                    st.warning("Enter an API key before saving.")
                else:
                    saved = config.save_secret("OPENROUTER_API_KEY", openrouter_api_key.strip())
                    os.chmod(saved, 0o600)
                    st.success(f"Saved to {saved.name} (owner-only permissions). "
                               "It will load automatically next time.")
            # Keep ollama values from config (not shown)
            ollama_host = config.ollama_host
            ollama_port = config.ollama_port
            ollama_model = config.ollama_model

        # Advanced settings
        st.markdown("---")
        st.subheader("Field Settings")
        st.caption("These controls shape the size of the 3D consciousness field "
                   "space that your state is plotted inside.")
        field_x = st.slider(
            "Arousal Range",
            5.0, 20.0, float(config.field_x_range), 1.0,
            help=("Width of the field along the Arousal axis — how far calm vs "
                  "activated states can travel. Larger = more room for extreme "
                  "moods. Axis note: +/-X on the map."),
        )
        field_y = st.slider(
            "Depth Range",
            5.0, 20.0, float(config.field_y_range), 1.0,
            help=("Height of the field along the Depth axis — how deep (unconscious) "
                  "vs surface (everyday) your reading can go. Larger = more depth "
                  "resolution. Axis note: +/-Y on the map."),
        )
        field_z = st.slider(
            "Openness Range",
            5.0, 20.0, float(config.field_z_range), 1.0,
            help=("Width of the field along the Openness axis — how closed/defensive "
                  "vs receptive/open your states can register.")
        )

        # Initialize engine (cache keyed on config values so switching
        # backend/model/field-range in the sidebar rebuilds it)
        @st.cache_resource
        def init_engine(backend_name, host, port, model, or_key, or_model, fx, fy, fz):
            # Override config from sidebar
            config.backend = backend_name
            config.ollama_host = host
            config.ollama_port = port
            config.ollama_model = model
            config.openrouter_api_key = or_key
            config.openrouter_model = or_model
            config.field_x_range = fx
            config.field_y_range = fy
            config.field_z_range = fz
            engine = LookingGlassEngine()
            renderer = FieldRenderer()
            return engine, renderer

        try:
            engine, renderer = init_engine(
                backend, ollama_host, ollama_port, ollama_model,
                openrouter_api_key, openrouter_model,
                field_x, field_y, field_z,
            )
        except Exception as e:
            st.error(f"Failed to initialize engine: {e}")
            st.stop()

        # User authentication
        st.markdown("---")
        st.subheader("Who Is Asking?")
        st.caption("Each user has their own password, session history, patterns, "
                   "and oracle voice.")
        _users = _list_users()
        auth_mode = st.radio(
            "Account",
            ["Log in", "New user"],
            horizontal=True,
            help="Pick an existing account to log in, or create a new one. "
                 "Each account keeps its own private session history.",
        )
        if auth_mode == "Log in":
            sel_user = st.selectbox(
                "Choose your name",
                _users if _users else ["(no accounts yet)"],
                help="Choose the account you want to open. Enter your password below.",
            )
            sel_password = st.text_input("Password", type="password", key="login_pw",
                                         help="Your password for this account.")
            if st.button("Open my mirror", key="login_btn",
                         help="Unlocks your private session history and oracle voice."):
                if sel_user.startswith("(") or not sel_password:
                    st.warning("Pick a name and enter your password.")
                elif engine.authenticate_user(sel_user, sel_password):
                    st.session_state["current_user"] = engine.current_user
                    st.success(f"Welcome back, {engine.current_user}.")
                else:
                    st.error("Incorrect password or unknown user.")
        else:
            new_user = st.text_input("New name", key="new_user_name",
                                     help="A name for your new account.")
            new_password = st.text_input("New password", type="password",
                                         key="new_user_pw",
                                         help="A password to protect this account.")
            if st.button("Create my mirror", key="create_btn",
                         help="Creates the account and signs you in."):
                if not new_user or not new_password:
                    st.warning("Enter a name and a password.")
                elif engine.create_user(new_user, new_password):
                    st.session_state["current_user"] = engine.current_user
                    st.success(f"Welcome, {engine.current_user}. Your mirror is yours.")
                else:
                    st.error("That name is taken. Pick another or log in.")
        if "current_user" not in st.session_state:
            st.session_state["current_user"] = "default"

        st.markdown("---")
        st.caption(f"Looking Glass Engine v{config.version}")
        st.caption("Everything runs locally — no data leaves your machine"
                   if backend == "ollama"
                   else "Using cloud OpenRouter backend — queries are sent to OpenRouter")

    # Main content area
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📝 Your Question")

        # Aether cast banner (once the persona is known)
        if engine.persona is not None:
            cast = engine.persona
            st.markdown(
                f'<div class="aether-cast">🜚 The oracle answers today as '
                f'<b>{cast.archetype_name}</b>'
                f'<span class="aether-reveal" title="The aether lot-casted this '
                f'voice from genuine chance (seed + time + your state as a bias). '
                f'Honest: you can reveal exactly how it was drawn.">ⓘ</span></div>',
                unsafe_allow_html=True,
            )
            with st.expander("Show how this voice was chosen"):
                st.caption(cast.reveal_text)

        question = st.text_area(
            "Ask the field anything",
            height=100,
            placeholder="What is the nature of consciousness?\nWhy am I here?\nWhat does this moment mean?",
            help="Type your question and press Enter or click 'Send'. The engine reads your state from how you write.",
        )

        # Optional state confirmation
        with st.expander("Correct my reading of your state (optional)"):
            st.caption("The oracle reads your state from your words, but you "
                       "know yourself best. Correct any axis to anchor the "
                       "response on what's really true for you.")
            c_a = st.number_input("Arousal (calm ↔ activated)", -10.0, 10.0, 0.0, 1.0, key="c_a")
            c_d = st.number_input("Depth (surface ↔ deep)", -10.0, 10.0, 0.0, 1.0, key="c_d")
            c_o = st.number_input("Self-disclosure (guarded ↔ receptive)", -10.0, 10.0, 0.0, 1.0, key="c_o")
            confirm_clicked = st.button("Use my corrections", key="confirm_state")
        confirmed_state = None
        if confirm_clicked:
            confirmed_state = {"arousal": c_a, "depth": c_d, "openness": c_o}

        col_send, col_clear = st.columns([1, 4])
        with col_send:
            send_clicked = st.button(
                "Send 🔮",
                use_container_width=True,
                type="primary",
                help=("Sends your question through the Looking Glass pipeline: "
                      "your text is analyzed for consciousness state, plotted on "
                      "the 3D field, and sent to the chosen backend (Ollama or "
                      "OpenRouter) to produce a field response."),
            )
        with col_clear:
            st.write("")  # spacer

        # Session intent mode + thread control
        mode = st.selectbox(
            "Session intent",
            ["General", "Process", "Lift", "Clarify", "Find Direction", "Calm"],
            index=["General", "Process", "Lift", "Clarify", "Find Direction", "Calm"].index(engine.mode)
            if engine.mode in ["General", "Process", "Lift", "Clarify", "Find Direction", "Calm"] else 0,
            help=("What you want this session to do for you. The oracle shapes "
                  "its focus and its takeaway around your intent. General is "
                  "open; Process works through a feeling; Lift savors the good; "
                  "Clarify untangles a decision; Find Direction draws out "
                  "values; Calm grounds and stills."),
        )
        if st.button("🔄 New thread",
                     help="Forget this session's conversation and start fresh. "
                          "The oracle keeps its voice but drops the thread "
                          "continuity so you can begin a new subject."):
            engine.reset_thread()

        if send_clicked and question.strip():
            with st.spinner("The field is listening..."):
                try:
                    history = engine.get_history(6)
                    result = engine.query(
                        question.strip(),
                        confirmed_state=confirmed_state,
                        mode=mode,
                        history=history,
                    )

                    # Store in session state
                    st.session_state.last_result = result
                    st.session_state.last_question = question.strip()
                    st.session_state.confirmed = confirmed_state is not None

                except Exception as e:
                    st.error(f"Error: {e}")
                    logger.error(f"Query error: {e}", exc_info=True)

    with col2:
        st.subheader("🗺️ Consciousness Field")

        # Show field map
        if hasattr(st.session_state, 'last_result') and st.session_state.last_result:
            result = st.session_state.last_result
            field = engine.field

            # State metrics
            state = result["state"]
            region = result["region"]

            # Field map
            field_html = render_field_map_html(field, state)
            st.markdown(field_html, unsafe_allow_html=True)

            st.markdown("### State Reading")
            st.caption("How the app read your consciousness from the way you wrote.")
            col_a, col_d, col_o = st.columns(3)
            with col_a:
                st.metric(
                    "Arousal", f"{state.arousal:+.2f}",
                    delta_color="inverse" if state.arousal < 0 else "normal",
                    help=("Arousal (X axis, -10 to +10): how calm vs activated your "
                          "state reads. Negative = calm/reflective, positive = "
                          "activated/energized. Derived from emotional tone, urgency "
                          "words, and typing pace in your question."),
                )
            with col_d:
                st.metric(
                    "Depth", f"{state.depth:+.2f}",
                    delta_color="normal" if state.depth > 0 else "inverse",
                    help=("Depth (Y axis, -10 to +10): how surface vs deep your "
                          "state reads. Positive = deep/contemplative, negative = "
                          "everyday/surface. Derived from abstract and contemplative "
                          "word use in your question."),
                )
            with col_o:
                st.metric(
                    "Self-disclosure", f"{state.openness:+.2f}",
                    delta_color="normal" if state.openness > 0 else "inverse",
                    help=("Self-disclosure (Z axis, -10 to +10): how guarded/"
                          "defensive vs receptive/open your state reads. "
                          "Positive = open, negative = guarded. An estimated "
                          "tendency from your question's framing — not a "
                          "measure of your personality."),
                )

            # Region badge
            css_class = get_region_css_class(region)
            st.markdown(
                f'<span class="region-badge {css_class}" title="The nearest named '
                f'region on the consciousness field to your current state reading. '
                f'This is the archetype your awareness is closest to right now.">'
                f'{region}</span>',
                unsafe_allow_html=True,
            )

            # Magnitude and confidence
            confirmed_tag = " (confirmed by you)" if result.get("confirmed") else ""
            method_tag = "valid offline reading" if result.get("reading_method") != "keyword" else "keyword fallback"
            st.caption(
                f"Magnitude: {state.magnitude():.2f}  |  Confidence: {state.confidence:.2f}"
                f"{confirmed_tag}",
                help=f"Magnitude = overall strength of your state reading. "
                     f"Confidence = how much text was available (0 to 1). "
                     f"Reading engine: {method_tag}. 'Confirmed by you' means you "
                     f"corrected this reading, so it anchors the response.",
            )

            # Resonance bars
            st.markdown("### Field Resonance")
            st.caption("How strongly your current state resonates with each "
                       "archetypal region — higher score = closer match.")
            resonance = result.get("resonance", {})
            if resonance:
                for name, score in sorted(resonance.items(), key=lambda x: x[1], reverse=True)[:5]:
                    st.markdown(
                        f'<span title="Resonance of your current state with the '
                        f'{name} archetype, from 0 (no match) to 1 (perfect match).">'
                        f'**{name}**</span>',
                        unsafe_allow_html=True,
                    )
                    st.progress(min(score, 1.0))
                    st.caption(f"Score: {score:.3f}")

        else:
            st.info("Ask a question to see your consciousness field map")

    # Response section (full width)
    if hasattr(st.session_state, 'last_result') and st.session_state.last_result:
        result = st.session_state.last_result

        st.markdown("---")
        st.subheader("🌊 Field Response")

        response = result.get("response", "")
        region = result.get("region", "")
        css_class = get_region_css_class(region)

        # Show region and response
        col_resp, col_meta = st.columns([3, 1])
        with col_resp:
            st.caption("The oracle's reflection — generated from your question "
                       "plus your state, spoken in this session's manifested "
                       "voice. Every reply ends with a takeaway to carry.")
            st.markdown(f'<div class="response-box">{response}</div>', unsafe_allow_html=True)
        with col_meta:
            persona_name = (result.get("persona") or {}).get("archetype_name") if result.get("persona") else None
            if persona_name:
                st.markdown(
                    f'<span class="region-badge region-transcendent" '
                    f'title="The personality the aether cast for this session. '
                    f'It stays the same for the whole session, then re-casts '
                    f'next time.">🜚 {persona_name}</span>',
                    unsafe_allow_html=True,
                )
            st.markdown(
                f'<span class="region-badge {css_class}" title="The archetypal '
                f'field region your state is closest to. Backend and model below '
                f'tell you which engine produced this response.">{region}</span>',
                unsafe_allow_html=True,
            )
            st.caption(f"User: {engine.current_user}")
            st.caption(f"Backend: {config.backend}",
                       help="Which engine produced the response — 'ollama' is your "
                            "local model, 'openrouter' is the cloud gateway.")
            st.caption(
                f"Model: {config.ollama_model if config.backend == 'ollama' else config.openrouter_model}",
                help="The specific model name behind this response.",)

    # Current thread (multi-turn continuity) — shown when the thread has turns
    if engine.conversation:
        with st.expander("🧵 This Thread"):
            st.caption("Your ongoing conversation with the oracle in this "
                       "session's voice. Keep asking follow-ups — the oracle "
                       "remembers what came before.")
            for i in range(0, len(engine.conversation), 2):
                if i < len(engine.conversation):
                    q = engine.conversation[i].get("content", "")
                    st.markdown(f"**You:** {q}")
                if i + 1 < len(engine.conversation):
                    a = engine.conversation[i + 1].get("content", "")
                    st.markdown(f"*Oracle:* {a[:400]}{'…' if len(a) > 400 else ''}")
                    st.markdown("---")

    # Session history in expander (scoped to current user)
    with st.expander("📊 Session History"):
        st.caption(f"Every question {engine.current_user} has asked, with the "
                   "state reading, region, and oracle voice at the time. Grows "
                   "over time so you can see how your state shifts across sessions.")
        history = engine.get_history(10)
        if history:
            for s in history:
                persona_tag = f" · 🜚 {s.get('persona', '')}" if s.get("persona") else ""
                st.markdown(f"**{s.get('timestamp', '')[:19]}** — {s.get('question', '')[:70]}...{persona_tag}")
                st.caption(f"Region: {s.get('state_region', 'N/A')} | "
                          f"Arousal: {s.get('state_arousal', 0):+.1f} | "
                          f"Depth: {s.get('state_depth', 0):+.1f} | "
                          f"Self-disc: {s.get('state_openness', 0):+.1f}")
                st.markdown("---")
        else:
            st.info(f"No sessions yet for '{engine.current_user}'. "
                    "Ask a question to start tracking.")

    # Pattern analysis (scoped to current user)
    with st.expander("🔍 Pattern Analysis"):
        st.caption(f"The oracle's long memory of {engine.current_user}: regions "
                   "visited most, recurring themes, and how the state has "
                   "shifted over time.")

        delta = engine.get_state_delta()
        if delta.get("has_delta"):
            st.markdown("**📈 Change over time**")
            st.caption(f"Across {delta['sessions']} sessions ({delta['from']} → {delta['to']}):")
            st.caption(f"• Arousal: {delta['arousal_delta']:+.1f}  "
                       f"• Depth: {delta['depth_delta']:+.1f}  "
                       f"• Self-disc: {delta['openness_delta']:+.1f}")

        regions = engine.get_pattern_regions()
        if regions:
            st.markdown("**🌍 Regions visited most**")
            for r in regions:
                st.markdown(f"- **{r.get('label', 'Unknown')}**: {r.get('visits', 0)} visits")

        themes = engine.get_recurring_themes()
        if themes:
            st.markdown("**🔁 Recurring themes in your words**")
            st.markdown(" — ".join(f"{t['word']}" for t in themes))

        if not regions and not themes and not delta.get("has_delta"):
            st.info("No pattern data yet. Keep asking questions to build your pattern.")

    # Distress / help note (honest limits)
    with st.expander("🛟 Not therapy — and where to get real help"):
        st.markdown(
            "The Looking Glass is a **reflection companion**, not a clinician. "
            "It never diagnoses or treats mental-health conditions, and it can "
            "misread you — that's why you can correct its state reading.\n\n"
            "If you're in crisis, feeling unsafe, or need real, human support, "
            "please reach out now:\n"
            "- **In Canada (all ages):** call or text **988** — suicide & crisis support, 24/7\n"
            "- **Calgary & Southern AB Distress Centre:** 24/7 phone, text & live chat\n"
            "  (search 'Distress Centre Calgary' online)\n"
            "- **Kids Help Phone (under 25):** available 24/7 across Canada\n"
            "- **If you are in immediate danger, call 911 (or your local emergency number).**",
            unsafe_allow_html=True,
        )

    # Footer
    st.markdown("---")
    st.caption("Looking Glass Engine — Software-only consciousness interface. "
               "No data leaves your machine. All processing is local.")


if __name__ == "__main__":
    main()