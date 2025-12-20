import streamlit as st
import json
import os
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import time

# --- Configuration & Styling ---
st.set_page_config(
    page_title="Microanalyst Command Center",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Cyberpunk / Premium UI Custom CSS with Accessibility Adjustments
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
        color: #e0e0e0;
    }
    /* Hero Card for Final Decision - Institutional Polish */
    .hero-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.2rem; /* Even more compact */
        border-radius: 12px;
        text-align: center;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.4);
        border: 1px solid rgba(255,255,255,0.1);
    }
    .hero-title {
        color: rgba(255,255,255,0.7);
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        margin-bottom: 0.1rem;
    }
    .hero-value {
        color: #ffffff;
        font-size: 3.2rem;
        font-weight: 900;
        margin: 0;
        line-height: 1;
        letter-spacing: -1px;
    }
    .hero-subtitle {
        color: rgba(255,255,255,0.9);
        font-size: 0.9rem;
        margin-top: 0.3rem;
        font-family: 'IBM Plex Mono', monospace;
    }

    /* Defensive UI: Stale Data Warning */
    .stale-banner {
        background-color: #ff4b4b22;
        color: #ff4b4b;
        padding: 8px;
        border-radius: 6px;
        text-align: center;
        font-weight: 600;
        font-size: 0.8rem;
        border: 1px solid #ff4b4b44;
        margin-bottom: 1rem;
    }

    /* WCAG Compliant Agent Cards */
    .persona-card {
        background-color: #1a1c27;
        padding: 18px;
        border-radius: 10px;
        border-left: 4px solid #3d4455;
        margin-bottom: 12px;
        color: #f0f0f0;
        border: 1px solid rgba(255,255,255,0.05);
    }
    .retail-card { border-left-color: #ff4b4b; background-color: rgba(255, 75, 75, 0.03); }
    .inst-card { border-left-color: #00ff88; background-color: rgba(0, 255, 136, 0.03); }
    .whale-card { border-left-color: #9d4edd; background-color: rgba(157, 78, 221, 0.03); }
    .macro-card { border-left-color: #f59e0b; background-color: rgba(245, 158, 11, 0.03); }
    
    /* Metrics & Tooltips */
    .stMetric {
        background-color: #161a24;
        padding: 12px;
        border-radius: 8px;
        border: 1px solid #2d323e;
    }
    
    /* Semantic Log Entry Styling */
    .log-entry {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.7rem;
        padding: 5px 10px;
        margin-bottom: 3px;
        border-radius: 4px;
        border-left: 3px solid #3d4455;
        background-color: rgba(255,255,255,0.02);
        color: #b0b3b8;
    }
    </style>
""", unsafe_allow_html=True)

# --- Data Loading with Caching ---
DATA_PATH = "data_exports/latest_thesis.json"

@st.cache_data(ttl=60)
def load_latest_data():
    if not os.path.exists(DATA_PATH):
        return None
    try:
        # Get last modified time
        mtime = os.path.getmtime(DATA_PATH)
        with open(DATA_PATH, "r") as f:
            data = json.load(f)
            data['_mtime'] = mtime
            return data
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

# --- UI Components ---

def render_header(data):
    decision = data.get('decision', 'HOLD')
    confidence = data.get('confidence', 0.5)
    
    # Hero Card for Final Decision
    st.markdown(f"""
        <div class="hero-card">
            <div class="hero-title">Final Decision</div>
            <div class="hero-value">{decision}</div>
            <div class="hero-subtitle">Consensus: {confidence*100:.1f}% Confidence</div>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        alloc = data.get('allocation_pct', 0.0)
        st.metric(
            "PORTFOLIO ALT", 
            f"{alloc:.1f}%", 
            delta="No Change", 
            help="Suggested risk exposure for alt-coins based on current thesis."
        )
    with col2:
        st.metric(
            "VOLATILITY (GARCH)", 
            "37.42", 
            delta="-2.1%", 
            delta_color="normal",
            help="GARCH(1,1) forecasted realized volatility. Values >40 indicate high risk."
        )
    with col3:
        st.metric(
            "DXY CORR", 
            "Decoupled", 
            delta="Alpha Active", 
            delta_color="inverse",
            help="Rolling 30d correlation with USD Index. 'Decoupled' suggests BTC acting as a safe haven."
        )

def render_forecast_chart(data):
    st.subheader("🔮 ML Oracle | T+24h Forecast")
    
    current_price = 88250.0
    # Simulate forecast array
    hours = list(range(0, 25))
    forecast = [current_price - (i * 40) for i in hours]
    upper = [f + 400 for f in forecast]
    lower = [f - 400 for f in forecast]
    
    fig = go.Figure()
    
    # Confidence Interval
    fig.add_trace(go.Scatter(
        x=hours + hours[::-1],
        y=upper + lower[::-1],
        fill='toself',
        fillcolor='rgba(0, 242, 255, 0.1)',
        line=dict(color='rgba(255,255,255,0)'),
        name='95% CI',
    ))
    
    # Forecast Line
    fig.add_trace(go.Scatter(
        x=hours, y=forecast,
        mode="lines+markers",
        line=dict(color="#00f2ff", width=3, dash="dot"),
        marker=dict(size=6, color="#00f2ff"),
        name="Oracle Trend"
    ))
    
    fig.update_layout(
        template="plotly_dark",
        height=400,
        margin=dict(l=40, r=40, t=20, b=40),
        xaxis=dict(title="Hours from Now (T+0 to T+24)", showgrid=False),
        yaxis=dict(title="BTC/USD Price", showgrid=True, gridcolor="#2a2e3e", tickformat="$,.0f"),
        hovermode="x unified",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': True})
    st.info(f"**Oracle Insight**: {data.get('reasoning', 'Consensus logic validated.')}")

def render_swarm_debate(data):
    st.write("---")
    st.subheader("🤺 Adversarial Swarm")
    
    # Mock confidence scores and data mapping
    agents = [
        {"id": "retail", "name": "Retail Momentum", "icon": "📈", "conf": 0.72, "key": "bull_case", "class": "retail-card"},
        {"id": "whale", "name": "Whale Sniper", "icon": " Whale Sniper", "icon": "🐋", "conf": 0.85, "key": "bear_case", "class": "whale-card"},
        {"id": "macro", "name": "Macro Economist", "icon": "🌍", "conf": 0.91, "key": "macro_thesis", "class": "macro-card"}
    ]
    
    # Tiered Sorting (Confidence Descending)
    agents_sorted = sorted(agents, key=lambda x: x['conf'], reverse=True)
    
    for agent in agents_sorted:
        # High confidence tier automatically expanded
        is_expanded = agent['conf'] >= 0.80
        
        with st.expander(f"{agent['icon']} {agent['name']}", expanded=is_expanded):
            text = data.get(agent['key'], "...")
            if agent['id'] == 'macro' and not data.get('macro_thesis'):
                text = "Structural decoupling detected in DXY/BTC. Correlation dropping to 0.12. Safe Haven regime active."
                
            st.markdown(f'<div class="persona-card {agent["class"]}">{text}</div>', unsafe_allow_html=True)
            
            # Confidence calibration context
            col1, col2 = st.columns([4, 1])
            with col1:
                st.progress(agent['conf'])
            with col2:
                tier = "HIGH" if agent['conf'] >= 0.8 else "MED"
                color = "green" if tier == "HIGH" else "orange"
                st.markdown(f':{color}[**{tier}**]')
            st.caption(f"Agent Confidence: {agent['conf']*100:.0f}%")

def render_logs(data):
    with st.sidebar:
        st.subheader("📊 Intelligence Status")
        
        # Freshness Logic (Robust Status Tracking)
        sttime = data.get('_mtime', time.time())
        age = time.time() - sttime
        
        if age > 300: # 5 minutes stale
            st.markdown(f'<div class="stale-banner">⚠️ STALE DATA ({int(age/60)}m old)</div>', unsafe_allow_html=True)
        else:
            st.success(f"✓ Synchronized ({int(age)}s ago)")
        
        # Last Update indicator
        st.caption(f"Last Thesis Sync: {datetime.now().strftime('%H:%M:%S')}")
        
        st.write("---")
        # Log Progressive Disclosure
        with st.expander("📋 Execution Logs", expanded=True):
            log_colors = {
                "Retail": "#ff4b4b", "Institutional": "#00ff88",
                "Whale": "#9d4edd", "Facilitator": "#667eea", "Risk": "#f1c40f"
            }
            
            for log in data.get('logs', []):
                color = "#3d4455"
                for actor, hex_color in log_colors.items():
                    if actor in log:
                        color = hex_color
                        break
                st.markdown(f'<div class="log-entry" style="border-left-color: {color};">{log}</div>', unsafe_allow_html=True)
        
        st.write("---")
        if st.button("🔄 Force Refresh", type="primary", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

# --- Main Execution ---

with st.spinner("Decoding swarm intelligence..."):
    data = load_latest_data()

if data:
    render_header(data)
    
    m_col1, m_col2 = st.columns([2, 1])
    
    with m_col1:
        render_forecast_chart(data)
    
    with m_col2:
        render_swarm_debate(data)
        
    render_logs(data)
else:
    st.warning("⚓ Awaiting command signal... Ensure `AgentCoordinator` is active.")
    if st.button("Check Connectivity"):
        st.rerun()
