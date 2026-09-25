import streamlit as st


def apply_molai_cule_style():
    st.markdown(
        """
        <style>

        /* =========================================================
           molAIcule GLOBAL DESIGN SYSTEM
           ========================================================= */

        /* ---------- Google Fonts ---------- */

        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');


        /* ---------- Global App ---------- */

        .stApp {
            background: #071426;
            color: #F5F3FF;
            font-family: 'Inter', sans-serif;
        }


        /* ---------- Main Content ---------- */

        .main .block-container {
            max-width: 1400px;
            padding-top: 2rem;
            padding-bottom: 4rem;
            padding-left: 3rem;
            padding-right: 3rem;
        }


        /* ---------- Sidebar ---------- */

        section[data-testid="stSidebar"] {
            background: #0D1B33;
            border-right: 1px solid #2E2A55;
        }

        section[data-testid="stSidebar"] > div {
            padding-top: 1.5rem;
        }


        /* ---------- Sidebar Text ---------- */

        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] label {
            font-family: 'Inter', sans-serif;
        }


        /* ---------- Headings ---------- */

        h1, h2, h3, h4 {
            font-family: 'Inter', sans-serif !important;
            color: #F5F3FF !important;
            letter-spacing: -0.02em;
        }

        h1 {
            font-weight: 700 !important;
        }

        h2 {
            font-weight: 600 !important;
        }

        h3 {
            font-weight: 600 !important;
        }


        /* ---------- Normal Text ---------- */

        p {
            color: #D8D3EA;
        }


        /* ---------- Technical / Code Text ---------- */

        code,
        pre,
        .technical-text {
            font-family: 'JetBrains Mono', monospace !important;
        }


        /* ---------- Cards ---------- */

        .molai-card {
            background: #171A3A;
            border: 1px solid #2E2A55;
            border-radius: 14px;
            padding: 1.25rem;
            margin-bottom: 1rem;
        }


        .molai-card:hover {
            border-color: #453C73;
        }


        /* ---------- Small Labels ---------- */

        .molai-label {
            color: #B7AECF;
            font-size: 0.75rem;
            font-weight: 600;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 0.35rem;
        }


        /* ---------- Large Values ---------- */

        .molai-value {
            color: #F5F3FF;
            font-size: 1.65rem;
            font-weight: 700;
            line-height: 1.2;
        }


        .molai-value-accent {
            color: #8B5CF6;
            font-size: 1.65rem;
            font-weight: 700;
            line-height: 1.2;
        }


        /* ---------- Muted Text ---------- */

        .molai-muted {
            color: #B7AECF;
            font-size: 0.85rem;
        }


        /* ---------- Primary Buttons ---------- */

        .stButton > button {
            background: #8B5CF6;
            color: #071426;
            border: none;
            border-radius: 9px;
            padding: 0.65rem 1.2rem;
            font-family: 'Inter', sans-serif;
            font-weight: 600;
            transition: all 0.2s ease;
        }


        .stButton > button:hover {
            background: #C4B5FD;
            color: #071426;
            border: none;
            transform: translateY(-1px);
        }


        .stButton > button:active {
            transform: translateY(0);
        }


        /* ---------- Inputs ---------- */

        .stTextInput input,
        .stTextArea textarea,
        .stNumberInput input {
            background: #0D1B33 !important;
            color: #F5F3FF !important;
            border: 1px solid #2E2A55 !important;
            border-radius: 9px !important;
            font-family: 'Inter', sans-serif !important;
        }


        .stTextInput input:focus,
        .stTextArea textarea:focus,
        .stNumberInput input:focus {
            border-color: #8B5CF6 !important;
            box-shadow: 0 0 0 1px #8B5CF6 !important;
        }


        /* ---------- Select Boxes ---------- */

        div[data-baseweb="select"] > div {
            background: #0D1B33 !important;
            border-color: #2E2A55 !important;
            border-radius: 9px !important;
        }


        /* ---------- Multiselect ---------- */

        div[data-baseweb="select"] span {
            color: #F5F3FF !important;
        }


        /* ---------- Tabs ---------- */

        button[data-baseweb="tab"] {
            font-family: 'Inter', sans-serif;
            color: #B7AECF;
        }


        button[data-baseweb="tab"][aria-selected="true"] {
            color: #8B5CF6 !important;
        }


        /* ---------- Expanders ---------- */

        div[data-testid="stExpander"] {
            background: #171A3A;
            border: 1px solid #2E2A55;
            border-radius: 12px;
        }


        /* ---------- Metrics ---------- */

        div[data-testid="stMetric"] {
            background: #171A3A;
            border: 1px solid #2E2A55;
            border-radius: 14px;
            padding: 1rem;
        }


        div[data-testid="stMetricLabel"] {
            color: #B7AECF !important;
        }


        div[data-testid="stMetricValue"] {
            color: #F5F3FF !important;
        }


        /* ---------- Dataframes ---------- */

        div[data-testid="stDataFrame"] {
            border: 1px solid #2E2A55;
            border-radius: 12px;
            overflow: hidden;
        }


        /* ---------- Alerts ---------- */

        div[data-testid="stAlert"] {
            border-radius: 10px;
        }


        /* ---------- Horizontal Divider ---------- */

        hr {
            border-color: #2E2A55 !important;
        }


        /* ---------- Status Badge ---------- */

        .molai-status {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.3rem 0.65rem;
            border-radius: 999px;
            background: #171A3A;
            border: 1px solid #2E2A55;
            color: #B7AECF;
            font-size: 0.75rem;
            font-weight: 600;
        }


        .molai-status-dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: #8B5CF6;
        }


        /* ---------- Hero Section ---------- */

        .molai-hero {
            background: #0D1B33;

            border: 1px solid #2E2A55;
            border-radius: 18px;
            padding: 2rem;
            margin-bottom: 1.5rem;
        }


        .molai-hero-title {
            font-size: 2.25rem;
            font-weight: 700;
            color: #F5F3FF;
            margin-bottom: 0.5rem;
            letter-spacing: -0.035em;
        }


        .molai-hero-subtitle {
            color: #B7AECF;
            font-size: 1rem;
            max-width: 760px;
            line-height: 1.6;
        }


        /* ---------- Section Header ---------- */

        .molai-section-title {
            color: #F5F3FF;
            font-size: 1.15rem;
            font-weight: 600;
            margin-top: 1.5rem;
            margin-bottom: 0.75rem;
        }


        /* ---------- Research Note ---------- */

        .molai-research-note {
            background: #0D1B33;
            border: 1px solid #2E2A55;
            border-left: 3px solid #8B5CF6;
            border-radius: 10px;
            padding: 1rem 1.1rem;
            margin-top: 1.5rem;
            color: #D8D3EA;
            font-size: 0.85rem;
            line-height: 1.6;
        }


        .molai-research-note strong {
            color: #F5F3FF;
        }


        /* ---------- AI Panel ---------- */

        .molai-ai-panel {
            background: linear-gradient(
                135deg,
                #1B1538 0%,
                #171A3A 100%
            );

            border: 1px solid #4A3B73;
            border-radius: 14px;
            padding: 1.25rem;
            margin-top: 1rem;
        }


        .molai-ai-label {
            color: #C4B5FD;
            font-size: 0.75rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }


        /* ---------- Score Cards ---------- */

        .molai-score-card {
            background: #171A3A;
            border: 1px solid #2E2A55;
            border-radius: 14px;
            padding: 1.2rem;
            height: 100%;
        }


        .molai-score-number {
            font-size: 1.8rem;
            font-weight: 700;
            color: #8B5CF6;
        }


        .molai-score-scale {
            color: #8F87AA;
            font-size: 0.75rem;
        }


        /* ---------- Responsive ---------- */

        @media (max-width: 900px) {

            .main .block-container {
                padding-left: 1.25rem;
                padding-right: 1.25rem;
            }

            .molai-hero {
                padding: 1.5rem;
            }

            .molai-hero-title {
                font-size: 1.8rem;
            }

        }


        </style>
        """,
        unsafe_allow_html=True
    )