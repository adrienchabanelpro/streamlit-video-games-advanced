# style.py
import streamlit as st


def apply_style() -> None:
    """Inject global CSS for the retro neon dark theme."""
    st.markdown(
        """
        <link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&family=Tiny5&display=swap" rel="stylesheet">
        <style>
        /* ---- Retro Neon Dark Theme ---- */

        /* Sidebar */
        [data-testid="stSidebar"] {
            background-color: #1A1A2E;
            border-right: 2px solid #00FFCC;
        }
        [data-testid="stSidebar"] * {
            color: #E0E0E0;
        }

        /* Headings — neon cyan with glow */
        h1, h2, h3, h4, h5, h6 {
            font-family: 'Tiny5', sans-serif !important;
            color: #00FFCC !important;
            text-shadow: 0 0 10px rgba(0, 255, 204, 0.5);
        }

        /* Body text */
        .stMarkdown, .stText, p, li, span {
            color: #E0E0E0;
        }

        /* Links */
        a {
            color: #FF6EC7 !important;
        }
        a:hover {
            color: #FFFF00 !important;
            text-shadow: 0 0 8px rgba(255, 255, 0, 0.6);
        }

        /* Buttons — neon pink accent */
        .stButton > button {
            background-color: transparent;
            color: #FF6EC7;
            border: 2px solid #FF6EC7;
            font-family: 'Press Start 2P', cursive;
            font-size: 12px;
            transition: all 0.3s;
        }
        .stButton > button:hover {
            background-color: #FF6EC7;
            color: #0D0D0D;
            box-shadow: 0 0 15px rgba(255, 110, 199, 0.6);
        }

        /* Metrics — neon glow */
        [data-testid="stMetric"] {
            background-color: #1A1A2E;
            border: 1px solid #00FFCC;
            border-radius: 8px;
            padding: 12px;
            box-shadow: 0 0 8px rgba(0, 255, 204, 0.2);
        }
        [data-testid="stMetricValue"] {
            color: #00FFCC !important;
            text-shadow: 0 0 6px rgba(0, 255, 204, 0.4);
        }
        [data-testid="stMetricLabel"] {
            color: #E0E0E0 !important;
        }

        /* Selectbox / number input */
        .stSelectbox label, .stNumberInput label, .stSlider label {
            color: #E0E0E0 !important;
        }

        /* Dataframe styling */
        .stDataFrame {
            border: 1px solid #00FFCC;
            border-radius: 4px;
        }

        /* Tabs */
        .stTabs [data-baseweb="tab"] {
            color: #E0E0E0;
        }
        .stTabs [aria-selected="true"] {
            color: #00FFCC !important;
            border-bottom-color: #00FFCC !important;
        }

        /* Divider lines */
        hr {
            border-color: #333366;
        }

        /* Spinner */
        .stSpinner > div {
            border-top-color: #FF6EC7 !important;
        }

        /* File uploader */
        [data-testid="stFileUploader"] {
            border: 1px dashed #00FFCC;
            border-radius: 8px;
            padding: 10px;
        }

        /* Warning / info / error boxes */
        .stAlert {
            border-radius: 8px;
        }

        /* Navigation items */
        [data-testid="stSidebarNav"] a {
            color: #E0E0E0 !important;
        }
        [data-testid="stSidebarNav"] a:hover {
            color: #00FFCC !important;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )
