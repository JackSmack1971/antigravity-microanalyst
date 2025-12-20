import streamlit as st

def inject_custom_css():
    st.markdown("""
        <style>
            /* Global Font & Background */
            @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
            
            html, body, [class*="css"] {
                font-family: 'JetBrains Mono', monospace;
                background-color: #050505; /* Deep Black */
                color: #e0e0e0;
            }
            
            /* Streamlit Main Container */
            .stApp {
                background-color: #050505;
                background-image: radial-gradient(circle at 50% 50%, #111 0%, #000 100%);
            }

            /* --- Widget: TerminalToggle (st.radio) --- */
            /* Hide the default radio circles */
            div[role="radiogroup"] label > div:first-child {
                display: none !important;
            }
            
            /* Container styling */
            div[role="radiogroup"] {
                background: rgba(0, 0, 0, 0.4);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 4px;
                gap: 4px;
                display: flex;
                width: fit-content;
                backdrop-filter: blur(4px);
            }

            /* Button Styling */
            div[role="radiogroup"] label {
                border-radius: 6px;
                padding: 4px 12px !important;
                margin: 0 !important;
                transition: all 0.2s ease;
                border: 1px solid transparent;
            }

            /* Inactive State */
            div[role="radiogroup"] label div[data-testid="stMarkdownContainer"] p {
                color: #6b7280; /* Gray-500 */
                font-size: 0.75rem;
                font-weight: 700;
                letter-spacing: 0.05em;
            }
            
            div[role="radiogroup"] label:hover {
                background: rgba(255, 255, 255, 0.05);
            }
             div[role="radiogroup"] label:hover div[data-testid="stMarkdownContainer"] p {
                color: #9ca3af; /* Gray-400 */
             }

            /* Active State (Green/Black) - Targeting aria-checked context if possible, 
               but Streamlit puts aria-checked on the internal input. 
               We rely on the background color Streamlit applies or specific class hacking.
               Actually, standard Streamlit radio active state isn't easily targetable via parent selector in pure CSS without :has()
               Using :has() which is supported in modern browsers (Chrome/Edge/Firefox/Safari).
            */
            div[role="radiogroup"] label:has(input[aria-checked="true"]) {
                background-color: #22c55e !important; /* Green-500 */
                box-shadow: 0 0 15px rgba(34, 197, 94, 0.4);
            }

            div[role="radiogroup"] label:has(input[aria-checked="true"]) div[data-testid="stMarkdownContainer"] p {
                color: #000000 !important;
            }

            /* --- Widget: Ghost Tabs (st.tabs) --- */
            /* Tab Container */
            .stTabs [data-baseweb="tab-list"] {
                gap: 16px;
                background-color: transparent;
                padding-bottom: 8px;
            }

            /* Remove top decoration/border */
            .stTabs [data-baseweb="tab-border"] {
                display: none;
            }
            
            .stTabs [data-baseweb="tab-highlight"] {
                display: none; /* Hide default highlight bar */
            }

            /* Tab Button */
            .stTabs [data-baseweb="tab"] {
                height: auto;
                padding: 8px 0;
                background-color: transparent !important;
                border: none !important;
                border-bottom: 2px solid transparent !important;
                margin: 0 !important;
            }

            /* Tab Text */
            .stTabs [data-baseweb="tab"] p {
                font-size: 0.75rem;
                font-family: 'JetBrains Mono', monospace;
                font-weight: 700;
                color: #6b7280;
            }

            /* Active Tab (Magenta) */
            .stTabs [data-baseweb="tab"][aria-selected="true"] {
                border-bottom: 2px solid #d946ef !important; /* Fuchsia-500 */
            }
            
            .stTabs [data-baseweb="tab"][aria-selected="true"] p {
                color: #e879f9 !important; /* Fuchsia-400 */
                text-shadow: 0 0 10px rgba(217, 70, 239, 0.3);
            }

            /* --- CyberCard Styles --- */
            .cyber-card {
                position: relative;
                border-radius: 12px;
                background: rgba(10, 10, 10, 0.7);
                backdrop-filter: blur(12px);
                -webkit-backdrop-filter: blur(12px);
                border: 1px solid rgba(255, 255, 255, 0.08);
                overflow: hidden;
                margin-bottom: 1rem;
                transition: transform 0.2s ease, box-shadow 0.2s ease;
            }
            
            .cyber-card:hover {
                transform: translateY(-2px);
            }
            
            .card-content {
                padding: 1.25rem;
                position: relative;
                z-index: 2;
            }
            
            /* Glow Borders */
            .neon-green-border:hover {
                border-color: rgba(0, 255, 65, 0.4);
                box-shadow: 0 0 15px rgba(0, 255, 65, 0.15);
            }
            
            .neon-pink-border:hover {
                border-color: rgba(255, 0, 255, 0.4);
                box-shadow: 0 0 15px rgba(255, 0, 255, 0.15);
            }
            
            .neon-gray-border:hover {
                border-color: rgba(150, 150, 150, 0.4);
                box-shadow: 0 0 15px rgba(150, 150, 150, 0.1);
            }

            /* Typography */
            .card-title {
                font-size: 0.75rem;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                color: #888;
                display: block;
                margin-bottom: 0.25rem;
            }
            
            .card-value {
                font-size: 1.5rem;
                font-weight: 700;
                line-height: 1.2;
                letter-spacing: -0.05em;
            }
            
            .card-footer {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-top: 0.5rem;
            }
            
            .card-subtext {
                font-size: 0.7rem;
                color: #666;
            }
            
            /* Status Pill */
            .status-pill {
                width: 6px;
                height: 6px;
                border-radius: 50%;
            }
            
            @keyframes pulse-live {
                0% { box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.7); }
                70% { box-shadow: 0 0 0 6px rgba(34, 197, 94, 0); }
                100% { box-shadow: 0 0 0 0 rgba(34, 197, 94, 0); }
            }
            
            .live-indicator {
                animation: pulse-live 2s infinite;
            }
            
            /* Scanline Effect */
            .scanline {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: linear-gradient(
                    to bottom,
                    transparent 50%,
                    rgba(0, 0, 0, 0.2) 51%,
                    transparent 52%
                );
                background-size: 100% 4px;
                opacity: 0.1;
                pointer-events: none;
                z-index: 1;
            }

            /* Glass Chart Containers */
            .glass-container {
                background: rgba(10, 10, 10, 0.5);
                backdrop-filter: blur(8px);
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 8px;
                padding: 10px;
                margin-bottom: 10px;
            }
            
            /* Remove standard spacing */
            .block-container {
                padding-top: 1rem; /* tighter top */
                padding-bottom: 2rem;
                max-width: 95rem; 
            }
            
            /* Hide Streamlit Header/Footer */
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            
            /* GRID ALIGNMENT FIX */
            /* Force equal spacing for headers */
            h3 {
                min-height: 24px;
                margin-top: 0 !important;
                padding-top: 0 !important;
                font-size: 1rem !important;
                border-bottom: 1px solid #333;
            }

        </style>
    """, unsafe_allow_html=True)
