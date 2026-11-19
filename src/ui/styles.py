import streamlit as st


def apply_theme():
    st.markdown(
        """
        <style>
        :root {
            --navy:#07111F; --charcoal:#111827; --panel:#FFFFFF;
            --panel-soft:#F7F9FC; --border:#DDE4EC; --text:#172033;
            --muted:#67748A; --teal:#18A999; --blue:#3568FF;
        }
        .stApp { background:#F4F7FB; color:var(--text); }
        [data-testid="stSidebar"] {
            background:var(--navy); border-right:1px solid #1B2A3D;
        }
        [data-testid="stSidebar"] * { color:#EAF0F7; }
        [data-testid="stSidebarNav"] { padding-top:0.6rem; }
        [data-testid="stSidebarNav"] a {
            border-radius:8px; margin:4px 10px; padding:7px 10px;
        }
        [data-testid="stSidebarNav"] a[aria-current="page"] {
            background:#17243A; border-left:3px solid #3DA9FC;
        }
        [data-testid="stHeader"] { background:transparent; }
        .block-container { max-width:1320px; padding-top:2rem; }
        h1,h2,h3,h4 { color:var(--text); letter-spacing:0; }
        .app-eyebrow { color:#3568FF; font-size:.78rem; font-weight:800; letter-spacing:.08em; text-transform:uppercase; }
        .app-title { font-size:2rem; line-height:1.15; margin:.15rem 0 .35rem; }
        .app-subtitle { color:var(--muted); font-size:.98rem; margin-bottom:1.4rem; }
        .kpi-card,.section-card,.info-card,.status-card {
            background:var(--panel); border:1px solid var(--border); border-radius:8px;
            box-shadow:0 8px 24px rgba(20,32,55,.06); padding:1.1rem;
        }
        .kpi-label { color:var(--muted); font-size:.78rem; font-weight:700; text-transform:uppercase; }
        .kpi-value { color:var(--text); font-size:1.75rem; font-weight:800; line-height:1.1; margin:.35rem 0; }
        .kpi-note { color:var(--muted); font-size:.82rem; }
        .section-title { font-size:1.08rem; font-weight:800; margin:0 0 .2rem; }
        .section-copy { color:var(--muted); font-size:.88rem; }
        .status-upcoming { display:inline-block; background:#FFF4D6; color:#9A6700; border:1px solid #F4DFA2; border-radius:999px; padding:.28rem .65rem; font-size:.76rem; font-weight:800; }
        .status-live { display:inline-block; background:#DCF7E9; color:#167A52; border:1px solid #B7E9CD; border-radius:999px; padding:.28rem .65rem; font-size:.76rem; font-weight:800; }
        div[data-testid="stMetric"] { background:white; border:1px solid var(--border); border-radius:8px; padding:1rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )
