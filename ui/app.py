"""
Looking Glass Engine — Streamlit GUI.

A web-based consciousness interface that runs in the browser.
Connects to the same engine backend as the CLI but provides
a visual, interactive experience.

Run with: streamlit run ui/app.py
"""

import streamlit as st
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

    # Sidebar configuration
    with st.sidebar:
        st.header("Configuration")

        # Backend selection
        backend = st.selectbox(
            "AI Backend",
            ["ollama", "openrouter"],
            index=0 if config.backend == "ollama" else 1,
            help="Choose between local Ollama or cloud OpenRouter",
        )

        # Ollama settings (shown when Ollama is selected)
        if backend == "ollama":
            ollama_host = st.text_input(
                "Ollama Host",
                value=config.ollama_host,
                help="Hostname or IP of your Ollama server",
            )
            ollama_port = int(st.number_input(
                "Ollama Port",
                value=float(config.ollama_port),
                min_value=1024.0,
                max_value=65535.0,
                step=1.0,
                help="Port where Ollama is listening",
            ))
            ollama_model = st.text_input(
                "Ollama Model",
                value=config.ollama_model,
                help="Model name from your Ollama container",
            )
        else:
            ollama_host = config.ollama_host
            ollama_port = config.ollama_port
            ollama_model = config.ollama_model

        # Advanced settings
        st.markdown("---")
        st.subheader("Field Settings")
        field_x = st.slider("Arousal Range", 5.0, 20.0, float(config.field_x_range), 1.0)
        field_y = st.slider("Depth Range", 5.0, 20.0, float(config.field_y_range), 1.0)
        field_z = st.slider("Openness Range", 5.0, 20.0, float(config.field_z_range), 1.0)

        # Session info
        st.markdown("---")
        st.caption("Looking Glass Engine v0.1.0")
        st.caption("Everything runs locally — no data leaves your machine")

    # Initialize engine (cache keyed on all config values so switching
    # backend/model/field-range in the sidebar rebuilds the engine)
    @st.cache_resource
    def init_engine(backend_name, host, port, model, fx, fy, fz):
        # Override config from sidebar
        config.backend = backend_name
        config.ollama_host = host
        config.ollama_port = port
        config.ollama_model = model
        config.field_x_range = fx
        config.field_y_range = fy
        config.field_z_range = fz

        engine = LookingGlassEngine()
        renderer = FieldRenderer()
        return engine, renderer

    try:
        engine, renderer = init_engine(
            backend, ollama_host, ollama_port, ollama_model,
            field_x, field_y, field_z,
        )
    except Exception as e:
        st.error(f"Failed to initialize engine: {e}")
        st.stop()

    # Main content area
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📝 Your Question")
        question = st.text_area(
            "Ask the field anything",
            height=100,
            placeholder="What is the nature of consciousness?\nWhy am I here?\nWhat does this moment mean?",
            help="Type your question and press Enter or click 'Send'. The engine reads your state from how you write.",
        )

        col_send, col_clear = st.columns([1, 4])
        with col_send:
            send_clicked = st.button("Send 🔮", use_container_width=True, type="primary")
        with col_clear:
            st.write("")  # spacer

        # Single query mode
        if send_clicked and question.strip():
            with st.spinner("The field is listening..."):
                try:
                    result = engine.query(question.strip())

                    # Store in session state
                    st.session_state.last_result = result
                    st.session_state.last_question = question.strip()

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
            col_a, col_d, col_o = st.columns(3)
            with col_a:
                st.metric("Arousal", f"{state.arousal:+.2f}",
                         delta_color="inverse" if state.arousal < 0 else "normal")
            with col_d:
                st.metric("Depth", f"{state.depth:+.2f}",
                         delta_color="normal" if state.depth > 0 else "inverse")
            with col_o:
                st.metric("Openness", f"{state.openness:+.2f}",
                         delta_color="normal" if state.openness > 0 else "inverse")

            # Region badge
            css_class = get_region_css_class(region)
            st.markdown(f'<span class="region-badge {css_class}">{region}</span>',
                       unsafe_allow_html=True)

            # Magnitude and confidence
            st.caption(f"Magnitude: {state.magnitude():.2f}  |  Confidence: {state.confidence:.2f}")

            # Resonance bars
            st.markdown("### Field Resonance")
            resonance = result.get("resonance", {})
            if resonance:
                for name, score in sorted(resonance.items(), key=lambda x: x[1], reverse=True)[:5]:
                    st.markdown(f"**{name}**")
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
            st.markdown(f'<div class="response-box">{response}</div>', unsafe_allow_html=True)
        with col_meta:
            st.markdown(f'<span class="region-badge {css_class}">{region}</span>',
                       unsafe_allow_html=True)
            st.caption(f"Backend: {config.backend}")
            st.caption(f"Model: {config.ollama_model if config.backend == 'ollama' else config.openrouter_model}")

    # Session history in expander
    with st.expander("📊 Session History"):
        history = engine.get_history(10)
        if history:
            for s in history:
                st.markdown(f"**{s.get('timestamp', '')[:19]}** — {s.get('question', '')[:80]}...")
                st.caption(f"Region: {s.get('state_region', 'N/A')} | "
                          f"Arousal: {s.get('state_arousal', 0):+.1f} | "
                          f"Depth: {s.get('state_depth', 0):+.1f} | "
                          f"Openness: {s.get('state_openness', 0):+.1f}")
                st.markdown("---")
        else:
            st.info("No sessions yet. Ask a question to start tracking.")

    # Pattern analysis
    with st.expander("🔍 Pattern Analysis"):
        regions = engine.get_pattern_regions()
        if regions:
            st.write("Frequently visited regions:")
            for r in regions:
                st.markdown(f"- **{r.get('label', 'Unknown')}**: {r.get('visits', 0)} visits ({r.get('probability', 0):.0%})")
        else:
            st.info("No pattern data yet. Keep asking questions to build your pattern.")

    # Footer
    st.markdown("---")
    st.caption("Looking Glass Engine — Software-only consciousness interface. "
               "No data leaves your machine. All processing is local.")


if __name__ == "__main__":
    main()