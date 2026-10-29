from html import escape
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st


# =========================================================
# CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="LearnMate | AI Classroom",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_URL = "http://127.0.0.1:8000"
LOG_DIR = Path("attendance_logs")
REAL_CSV = LOG_DIR / "attendance_log.csv"
DEMO_CSV = LOG_DIR / "demo_attendance.csv"

LOG_DIR.mkdir(parents=True, exist_ok=True)

# Palette
VIOLET = "#6366F1"
CYAN = "#2DD4BF"
EMERALD = "#34D399"
AMBER = "#FBBF24"
ROSE = "#F87171"
MUTED = "#94A3B8"

STATUS_COLORS = {
    "Present": EMERALD,
    "Pending": AMBER,
    "Absent": ROSE,
    "Unknown": MUTED,
}


# =========================================================
# DATA HELPERS
# =========================================================

def ensure_demo_data():
    """Create illustrative demo records without overwriting them."""
    if DEMO_CSV.exists():
        return

    rows = [
        ["DEMO-001", "P0001", "Present", 1780, "2026-10-16T09:00:00", "2026-10-16T09:30:00"],
        ["DEMO-001", "P0002", "Present", 1650, "2026-10-16T09:00:00", "2026-10-16T09:30:00"],
        ["DEMO-001", "P0003", "Pending", 420, "2026-10-16T09:00:00", "2026-10-16T09:30:00"],
        ["DEMO-001", "P0004", "Pending", 300, "2026-10-16T09:00:00", "2026-10-16T09:30:00"],
        ["DEMO-002", "P0001", "Present", 2100, "2026-10-18T10:00:00", "2026-10-18T10:35:00"],
        ["DEMO-002", "P0002", "Present", 1950, "2026-10-18T10:00:00", "2026-10-18T10:35:00"],
        ["DEMO-002", "P0003", "Present", 1600, "2026-10-18T10:00:00", "2026-10-18T10:35:00"],
        ["DEMO-002", "P0005", "Pending", 500, "2026-10-18T10:00:00", "2026-10-18T10:35:00"],
        ["DEMO-003", "P0001", "Present", 2400, "2026-10-19T11:00:00", "2026-10-19T11:40:00"],
        ["DEMO-003", "P0002", "Pending", 800, "2026-10-19T11:00:00", "2026-10-19T11:40:00"],
        ["DEMO-003", "P0004", "Present", 2200, "2026-10-19T11:00:00", "2026-10-19T11:40:00"],
        ["DEMO-003", "P0005", "Present", 2050, "2026-10-19T11:00:00", "2026-10-19T11:40:00"],
    ]

    columns = [
        "session_id",
        "participant_id",
        "status",
        "presence_duration_seconds",
        "session_started_at",
        "session_ended_at",
    ]

    pd.DataFrame(rows, columns=columns).to_csv(DEMO_CSV, index=False)


def read_csv_safely(path):
    if not path.exists():
        return pd.DataFrame()

    try:
        return pd.read_csv(path)
    except (OSError, pd.errors.ParserError, UnicodeDecodeError):
        return pd.DataFrame()


def load_real_history():
    return read_csv_safely(REAL_CSV)


def load_demo_history():
    ensure_demo_data()
    return read_csv_safely(DEMO_CSV)


def api_get(path):
    response = requests.get(f"{API_URL}{path}", timeout=5)
    response.raise_for_status()
    return response.json()


def api_post(path):
    response = requests.post(f"{API_URL}{path}", timeout=10)
    response.raise_for_status()
    return response.json()


def duration_column(data):
    for column in (
        "presence_duration_seconds",
        "duration_seconds",
        "presence_duration",
    ):
        if column in data.columns:
            return column
    return None


def fmt_minutes(seconds):
    if seconds is None or pd.isna(seconds):
        return "N/A"
    return f"{seconds / 60:.0f} min"


# =========================================================
# UI HELPERS
# =========================================================

def style_chart(fig, height=340):
    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Plus Jakarta Sans, Inter, sans-serif", color="#CBD5E1", size=12),
        margin=dict(t=50, b=25, l=15, r=15),
        legend_title_text="",
        legend=dict(font=dict(color="#CBD5E1")),
        title=dict(font=dict(size=15, color="#F1F5F9"), x=0.02),
        xaxis=dict(gridcolor="rgba(255,255,255,0.05)", zerolinecolor="rgba(255,255,255,0.08)", color="#94A3B8"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.05)", zerolinecolor="rgba(255,255,255,0.08)", color="#94A3B8"),
        hoverlabel=dict(bgcolor="#0F172A", font_color="#F1F5F9", bordercolor="#334155"),
    )
    return fig


def section(title, subtitle=""):
    sub = f'<div class="sec-sub">{escape(subtitle)}</div>' if subtitle else ""
    st.markdown(
        f'<div class="sec"><div class="sec-title">{escape(title)}</div>{sub}</div>',
        unsafe_allow_html=True,
    )


def kpi(label, value, hint, icon, accent):
    return (
        f'<div class="kpi" style="--accent:{accent}">'
        f'<div class="kpi-icon">{icon}</div>'
        f'<div class="kpi-label">{escape(label)}</div>'
        f'<div class="kpi-value">{escape(str(value))}</div>'
        f'<div class="kpi-hint">{escape(hint)}</div>'
        f'</div>'
    )


def kpi_row(items):
    cols = st.columns(len(items))
    for col, item in zip(cols, items):
        col.markdown(kpi(*item), unsafe_allow_html=True)


def pill(text, color):
    return (
        f'<span class="pill" style="--c:{color}">'
        f'<span class="dot"></span>{escape(str(text))}</span>'
    )


def banner(text, tone="info"):
    icon = {"info": "✨", "warn": "⚠️", "ok": "✅"}.get(tone, "✨")
    st.markdown(
        f'<div class="banner {tone}"><span>{icon}</span><span>{escape(text)}</span></div>',
        unsafe_allow_html=True,
    )


def empty_state(icon, title, text):
    st.markdown(
        f'<div class="empty"><div class="empty-icon">{icon}</div>'
        f'<div class="empty-title">{escape(title)}</div>'
        f'<div class="empty-text">{escape(text)}</div></div>',
        unsafe_allow_html=True,
    )


def status_color(status):
    return STATUS_COLORS.get(str(status).title(), MUTED)


def show_table(data, max_rows=200):
    """Render a dataframe as a dark glass HTML table (no white canvas)."""
    if data is None or data.empty:
        empty_state("🗒️", "Nothing to show", "No rows available yet.")
        return

    view = data.head(max_rows)
    head = "".join(
        f"<th>{escape(str(c).replace('_', ' '))}</th>" for c in view.columns
    )

    body = []
    for _, row in view.iterrows():
        cells = []
        for col in view.columns:
            val = row[col]
            if pd.isna(val):
                cells.append('<td><span class="na">—</span></td>')
            elif str(col).lower() == "status":
                cells.append(f"<td>{pill(str(val).title(), status_color(val))}</td>")
            elif pd.api.types.is_number(val) and not isinstance(val, bool):
                num = float(val)
                txt = f"{int(num):,}" if num == int(num) else f"{num:,.1f}"
                cells.append(f'<td class="num">{txt}</td>')
            else:
                cells.append(f"<td>{escape(str(val))}</td>")
        body.append("<tr>" + "".join(cells) + "</tr>")

    note = ""
    if len(data) > max_rows:
        note = f'<div class="tbl-note">Showing first {max_rows} of {len(data):,} rows</div>'

    st.markdown(
        f'<div class="tbl-wrap"><table class="tbl"><thead><tr>{head}</tr></thead>'
        f'<tbody>{"".join(body)}</tbody></table></div>{note}',
        unsafe_allow_html=True,
    )


# =========================================================
# DESIGN — MIDNIGHT PLUM AURORA (DARK)
# =========================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Sora:wght@500;700&display=swap');

:root {
    --bg: #0A0914;
    --glass: rgba(255,255,255,0.045);
    --glass-strong: rgba(255,255,255,0.075);
    --line: rgba(255,255,255,0.09);
    --text: #F1F5F9;
    --muted: #94A3B8;
    --violet: #6366F1;
    --cyan: #2DD4BF;
    --emerald: #34D399;
}

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', Inter, sans-serif;
}

.stApp {
    background:
        radial-gradient(900px 500px at 8% -5%, rgba(99,102,241,0.28), transparent 60%),
        radial-gradient(800px 500px at 100% 0%, rgba(45,212,191,0.18), transparent 60%),
        radial-gradient(700px 500px at 50% 110%, rgba(244,114,182,0.14), transparent 60%),
        var(--bg);
    color: var(--text);
}

[data-testid="stHeader"] { background: transparent; }

[data-testid="stMainBlockContainer"] {
    padding-top: 1.6rem;
    padding-bottom: 3rem;
    max-width: 1320px;
}

/* ---------- Sidebar ---------- */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, rgba(20,18,43,0.94), rgba(7,11,20,0.96));
    border-right: 1px solid var(--line);
    backdrop-filter: blur(18px);
}
[data-testid="stSidebar"] * { color: #E2E8F0; }

.brand {
    display: flex; align-items: center; gap: 12px;
    padding: 6px 4px 4px 4px;
}
.brand-logo {
    width: 44px; height: 44px; border-radius: 14px;
    display: grid; place-items: center; font-size: 22px;
    background: linear-gradient(135deg, var(--violet), var(--cyan));
    box-shadow: 0 8px 24px rgba(99,102,241,0.45);
}
.brand-name {
    font-family: 'Sora', sans-serif;
    font-size: 21px; font-weight: 700; letter-spacing: -0.4px; color: #fff;
}
.brand-tag { font-size: 10px; letter-spacing: 2px; color: var(--muted); font-weight: 700; }

.side-label {
    font-size: 10.5px; letter-spacing: 2px; font-weight: 800;
    color: #64748B; margin: 18px 0 6px 4px;
}

[data-testid="stSidebar"] hr { border-color: var(--line); }

[data-testid="stSidebar"] [role="radiogroup"] { gap: 4px; }
[data-testid="stSidebar"] [role="radiogroup"] label {
    border-radius: 12px; padding: 10px 14px; width: 100%;
    border: 1px solid transparent;
    transition: all .18s ease;
}
[data-testid="stSidebar"] [role="radiogroup"] label > div:first-child { display: none; }
[data-testid="stSidebar"] [role="radiogroup"] label:hover {
    background: var(--glass-strong);
    transform: translateX(3px);
}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
    background: linear-gradient(90deg, rgba(99,102,241,0.35), rgba(45,212,191,0.14));
    border: 1px solid rgba(99,102,241,0.55);
    box-shadow: 0 6px 22px rgba(99,102,241,0.22);
}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p {
    color: #fff; font-weight: 700;
}

/* ---------- Typography ---------- */
h1, h2, h3, h4 { color: var(--text); letter-spacing: -0.3px; }
p, label, [data-testid="stCaptionContainer"] { color: var(--muted); }

.sec { margin: 26px 0 12px 0; }
.sec-title {
    font-family: 'Sora', sans-serif;
    font-size: 20px; font-weight: 700; color: var(--text);
    display: flex; align-items: center; gap: 10px;
}
.sec-title::before {
    content: ""; width: 5px; height: 20px; border-radius: 4px;
    background: linear-gradient(180deg, var(--violet), var(--cyan));
}
.sec-sub { color: var(--muted); font-size: 13px; margin: 4px 0 0 15px; }

/* ---------- Hero ---------- */
.hero {
    position: relative; overflow: hidden;
    padding: 34px 38px; border-radius: 26px;
    border: 1px solid var(--line);
    background:
        linear-gradient(120deg, rgba(99,102,241,0.30), rgba(45,212,191,0.14) 55%, rgba(244,114,182,0.22)),
        var(--glass);
    backdrop-filter: blur(16px);
    box-shadow: 0 20px 60px rgba(0,0,0,0.45);
    margin-bottom: 22px;
}
.hero::after {
    content: ""; position: absolute; right: -60px; top: -60px;
    width: 280px; height: 280px; border-radius: 50%;
    background: radial-gradient(circle, rgba(45,212,191,0.35), transparent 70%);
    animation: float 7s ease-in-out infinite;
}
@keyframes float {
    0%,100% { transform: translate(0,0) scale(1); }
    50% { transform: translate(-24px,18px) scale(1.12); }
}
.eyebrow {
    display: inline-block; padding: 5px 12px; border-radius: 999px;
    font-size: 10.5px; letter-spacing: 2.2px; font-weight: 800;
    color: #A5B4FC; background: rgba(99,102,241,0.18);
    border: 1px solid rgba(99,102,241,0.4);
}
.hero-title {
    font-family: 'Sora', sans-serif;
    font-size: 44px; line-height: 1.08; font-weight: 700;
    margin-top: 14px; letter-spacing: -1.2px;
    background: linear-gradient(90deg, #fff 10%, #FBCFE8 55%, #A5B4FC);
    -webkit-background-clip: text; background-clip: text; color: transparent;
}
.hero-sub { color: #CBD5E1; margin-top: 10px; font-size: 15px; max-width: 560px; }
.hero-chips { margin-top: 18px; display: flex; gap: 10px; flex-wrap: wrap; position: relative; z-index: 2; }

/* ---------- Pills / chips ---------- */
.pill {
    display: inline-flex; align-items: center; gap: 7px;
    padding: 5px 12px; border-radius: 999px; font-size: 12px; font-weight: 700;
    color: var(--c); background: color-mix(in srgb, var(--c) 14%, transparent);
    border: 1px solid color-mix(in srgb, var(--c) 40%, transparent);
}
.pill .dot {
    width: 7px; height: 7px; border-radius: 50%; background: var(--c);
    box-shadow: 0 0 10px var(--c);
}

/* ---------- KPI cards ---------- */
.kpi {
    position: relative; overflow: hidden;
    padding: 20px 20px 18px 20px; border-radius: 20px;
    background: var(--glass); border: 1px solid var(--line);
    backdrop-filter: blur(14px);
    transition: transform .2s ease, border-color .2s ease, box-shadow .2s ease;
}
.kpi::before {
    content: ""; position: absolute; inset: 0 0 auto 0; height: 3px;
    background: linear-gradient(90deg, var(--accent), transparent);
}
.kpi:hover {
    transform: translateY(-4px);
    border-color: var(--accent);
    box-shadow: 0 14px 40px color-mix(in srgb, var(--accent) 28%, transparent);
}
.kpi-icon {
    width: 40px; height: 40px; border-radius: 12px; display: grid; place-items: center;
    font-size: 19px; margin-bottom: 14px;
    background: color-mix(in srgb, var(--accent) 18%, transparent);
}
.kpi-label { font-size: 11.5px; letter-spacing: 1.2px; font-weight: 700; color: var(--muted); text-transform: uppercase; }
.kpi-value {
    font-family: 'Sora', sans-serif;
    font-size: 36px; font-weight: 700; color: #fff; line-height: 1.15; margin-top: 4px;
}
.kpi-hint { font-size: 12px; color: #64748B; margin-top: 2px; }

/* ---------- Participant cards ---------- */
.pcard {
    padding: 16px 18px; border-radius: 18px; margin-bottom: 14px;
    background: var(--glass); border: 1px solid var(--line);
    transition: all .2s ease;
}
.pcard:hover { transform: translateY(-3px); background: var(--glass-strong); }
.pcard-top { display: flex; align-items: center; gap: 12px; }
.avatar {
    width: 44px; height: 44px; border-radius: 14px; display: grid; place-items: center;
    font-weight: 800; font-size: 15px; color: #fff;
    background: linear-gradient(135deg, var(--violet), var(--cyan));
}
.pname { font-weight: 700; color: #fff; font-size: 15px; }
.psub { font-size: 12px; color: var(--muted); }
.bar { height: 7px; border-radius: 99px; background: rgba(255,255,255,0.07); margin-top: 14px; overflow: hidden; }
.bar > span { display: block; height: 100%; border-radius: 99px;
    background: linear-gradient(90deg, var(--violet), var(--cyan)); }
.bar-meta { display: flex; justify-content: space-between; font-size: 11.5px; color: var(--muted); margin-top: 6px; }

/* ---------- Insight cards ---------- */
.icard {
    height: 100%; padding: 20px; border-radius: 20px; margin-bottom: 14px;
    background: var(--glass); border: 1px solid var(--line);
    transition: all .2s ease;
}
.icard:hover { border-color: var(--tint); transform: translateY(-3px); }
.icard-icon {
    width: 42px; height: 42px; border-radius: 13px; display: grid; place-items: center;
    font-size: 20px; margin-bottom: 12px;
    background: color-mix(in srgb, var(--tint) 18%, transparent);
}
.icard-title { font-weight: 800; color: #fff; font-size: 16px; margin-bottom: 8px; }
.icard ul { margin: 0; padding-left: 18px; color: #CBD5E1; font-size: 13.5px; line-height: 1.7; }

/* ---------- Banner / empty ---------- */
.banner {
    display: flex; gap: 12px; align-items: center;
    padding: 12px 18px; border-radius: 14px; margin-bottom: 16px;
    font-size: 13.5px; color: #E2E8F0;
    border: 1px solid rgba(99,102,241,0.4);
    background: linear-gradient(90deg, rgba(99,102,241,0.16), rgba(45,212,191,0.06));
}
.banner.warn { border-color: rgba(251,191,36,0.45); background: rgba(251,191,36,0.1); }
.banner.ok { border-color: rgba(52,211,153,0.45); background: rgba(52,211,153,0.1); }

.empty {
    text-align: center; padding: 44px 20px; border-radius: 20px;
    border: 1.5px dashed rgba(255,255,255,0.14); background: var(--glass);
}
.empty-icon { font-size: 40px; }
.empty-title { font-weight: 800; color: #fff; font-size: 17px; margin-top: 8px; }
.empty-text { color: var(--muted); font-size: 13.5px; margin-top: 4px; }

/* ---------- Buttons ---------- */
.stButton > button,
[data-testid="stDownloadButton"] button {
    min-height: 44px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.12);
    background: var(--glass-strong); color: #fff !important; font-weight: 700;
    transition: all .2s ease;
}
.stButton > button:hover,
[data-testid="stDownloadButton"] button:hover {
    background: linear-gradient(90deg, var(--violet), #EC4899);
    border-color: transparent;
    box-shadow: 0 8px 26px rgba(99,102,241,0.45);
    transform: translateY(-2px);
    color: #fff !important;
}

/* ---------- Data + charts ---------- */
[data-testid="stDataFrame"], [data-testid="stTable"] {
    border: 1px solid var(--line); border-radius: 16px; overflow: hidden;
    background: var(--glass);
}
[data-testid="stPlotlyChart"] {
    background: var(--glass); border: 1px solid var(--line);
    border-radius: 20px; padding: 10px; backdrop-filter: blur(12px);
}

[data-baseweb="select"] > div,
[data-baseweb="input"] > div,
[data-baseweb="textarea"] > div {
    border-radius: 12px; border-color: var(--line); background-color: rgba(255,255,255,0.05);
}

[data-testid="stAlert"] { border-radius: 14px; }
hr { border-color: var(--line) !important; }

.foot { text-align: center; color: #475569; font-size: 12px; margin-top: 30px; }

/* ---------- Custom tables ---------- */
.tbl-wrap {
    max-height: 430px; overflow: auto; border-radius: 18px;
    border: 1px solid var(--line);
    background: linear-gradient(180deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02));
    backdrop-filter: blur(12px);
    box-shadow: 0 10px 30px rgba(0,0,0,0.35);
    margin-bottom: 8px;
}
table.tbl { width: 100%; border-collapse: separate; border-spacing: 0; font-size: 13px; }
table.tbl thead th {
    position: sticky; top: 0; z-index: 2; text-align: left; white-space: nowrap;
    padding: 13px 16px; font-size: 10.5px; letter-spacing: 1.4px; text-transform: uppercase;
    font-weight: 800; color: #A5B4FC;
    background: #15132B; border-bottom: 1px solid rgba(99,102,241,0.45);
}
table.tbl tbody td {
    padding: 12px 16px; color: #E2E8F0; white-space: nowrap;
    border-bottom: 1px solid rgba(255,255,255,0.05);
    transition: background .15s ease;
}
table.tbl tbody tr:nth-child(even) td { background: rgba(255,255,255,0.025); }
table.tbl tbody tr:hover td { background: rgba(99,102,241,0.16); }
table.tbl tbody tr:last-child td { border-bottom: none; }
table.tbl tbody td:first-child { font-weight: 700; color: #fff; }
table.tbl td.num { font-variant-numeric: tabular-nums; color: #5EEAD4; font-weight: 600; }
table.tbl .na { color: #475569; }
.tbl-note { color: #64748B; font-size: 12px; margin: 2px 4px 12px 4px; }

::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.15); border-radius: 8px; }
</style>
""", unsafe_allow_html=True)


# =========================================================
# LOAD DATA
# =========================================================

real_history = load_real_history()
demo_history = load_demo_history()

using_demo = real_history.empty
display_history = demo_history.copy() if using_demo else real_history.copy()

backend_ok = False
participants = []
backend_error = None

try:
    live_data = api_get("/attendance")
    participants = live_data.get("participants", [])
    backend_ok = True
except requests.RequestException as exc:
    backend_error = str(exc)

live_df = pd.DataFrame(participants)


# =========================================================
# SIDEBAR
# =========================================================

NAV = {
    "🏠  Overview": "Overview",
    "📡  Live Attendance": "Live Attendance",
    "🗂️  Session History": "Session History",
    "📈  Engagement Analytics": "Engagement Analytics",
    "💡  Instructor Insights": "Instructor Insights",
    "🧑‍🎓  Student Summary": "Student Summary",
}

with st.sidebar:
    st.markdown(
        '<div class="brand"><div class="brand-logo">🎓</div>'
        '<div><div class="brand-name">LearnMate</div>'
        '<div class="brand-tag">AI CLASSROOM</div></div></div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="side-label">NAVIGATE</div>', unsafe_allow_html=True)
    page = NAV[st.radio("Navigation", list(NAV.keys()), label_visibility="collapsed")]

    st.markdown('<div class="side-label">SESSION CONTROL</div>', unsafe_allow_html=True)

    if st.button("▶  Start Attendance", use_container_width=True):
        try:
            result = api_post("/attendance/start")
            st.success(result.get("message", "Start request completed"))
        except requests.RequestException as exc:
            st.error(f"Could not start attendance: {exc}")

    if st.button("■  Stop Attendance", use_container_width=True):
        try:
            result = api_post("/attendance/stop")
            st.success(result.get("message", "Stop request completed"))
        except requests.RequestException as exc:
            st.error(f"Could not stop attendance: {exc}")

    if st.button("↻  Refresh Dashboard", use_container_width=True):
        st.rerun()

    st.markdown('<div class="side-label">SYSTEM</div>', unsafe_allow_html=True)
    st.markdown(
        pill("Backend online", EMERALD) if backend_ok else pill("Backend offline", ROSE),
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div style='height:8px'></div>"
        + (pill("Demo data", AMBER) if using_demo else pill("Live data", CYAN)),
        unsafe_allow_html=True,
    )


# =========================================================
# HERO
# =========================================================

hero_chips = (
    pill("Backend online" if backend_ok else "Backend offline", EMERALD if backend_ok else ROSE)
    + " "
    + pill("Demo mode" if using_demo else "Live records", AMBER if using_demo else CYAN)
)

st.markdown(
    f"""
<div class="hero">
<div class="eyebrow">CLASSROOM INTELLIGENCE PLATFORM</div>
<div class="hero-title">Your classroom,<br>in perfect focus.</div>
<div class="hero-sub">Attendance operations, session history and teaching insights — beautifully unified in one workspace.</div>
<div class="hero-chips">{hero_chips}</div>
</div>
""",
    unsafe_allow_html=True,
)

if using_demo:
    banner(
        "Demo mode: illustrative records are shown because no real attendance "
        "history has been saved yet. Demo records are not real student attendance.",
        "info",
    )


# =========================================================
# OVERVIEW
# =========================================================

if page == "Overview":
    present_count = 0
    if "status" in live_df.columns:
        present_count = int(live_df["status"].astype(str).str.lower().eq("present").sum())

    record_count = len(display_history)
    session_count = (
        int(display_history["session_id"].nunique())
        if "session_id" in display_history.columns
        else 0
    )

    kpi_row([
        ("Live Participants", len(live_df), "detected right now", "📡", CYAN),
        ("Marked Present", present_count, "confirmed live", "✅", EMERALD),
        ("Historical Records", record_count, "across all sessions", "🗃️", VIOLET),
        ("Sessions Recorded", session_count, "saved to history", "🎬", AMBER),
    ])

    left, right = st.columns([1.3, 1])

    with left:
        section("Current Attendance", "Real-time view from the camera backend")
        if not live_df.empty:
            show_table(live_df)
        else:
            empty_state(
                "📷",
                "No live participants yet",
                "Start attendance and keep a face visible to the camera.",
            )

    with right:
        section("Attendance Status", "Share of records by status")

        chart_source = live_df
        chart_is_demo = False

        if (
            chart_source.empty
            or "status" not in chart_source.columns
            or chart_source["status"].nunique() < 2
        ):
            chart_source = display_history
            chart_is_demo = using_demo

        if not chart_source.empty and "status" in chart_source.columns:
            status_data = (
                chart_source["status"]
                .fillna("Unknown")
                .astype(str)
                .str.title()
                .value_counts()
                .rename_axis("Status")
                .reset_index(name="Records")
            )

            fig = px.pie(
                status_data,
                names="Status",
                values="Records",
                hole=0.7,
                color="Status",
                color_discrete_map=STATUS_COLORS,
            )
            fig.update_traces(
                textinfo="percent",
                marker=dict(line=dict(color="#0A0914", width=3)),
            )
            total = int(status_data["Records"].sum())
            fig.add_annotation(
                text=f"<b>{total}</b><br><span style='font-size:11px;color:#94A3B8'>records</span>",
                showarrow=False,
                font=dict(size=28, color="#FFFFFF"),
            )
            style_chart(fig, 330)
            st.plotly_chart(fig, use_container_width=True)

            if chart_is_demo:
                st.caption("Illustrative demo attendance distribution.")
        else:
            empty_state("📊", "Nothing to chart yet", "Attendance status appears once records exist.")

    section("Recent Attendance History", "Latest 10 records")
    show_table(display_history.tail(10))


# =========================================================
# LIVE ATTENDANCE
# =========================================================

elif page == "Live Attendance":
    section("Live Attendance", "Use the sidebar to start/stop, then refresh for the latest records")

    if not backend_ok:
        banner("Backend is unavailable. Start FastAPI first.", "warn")
        if backend_error:
            st.caption(backend_error)

    elif live_df.empty:
        empty_state(
            "🎥",
            "Waiting for participants",
            "Start a session, keep your face visible and refresh this page.",
        )

    else:
        filtered_live = live_df

        if "participant_id" in live_df.columns:
            participant_ids = sorted(live_df["participant_id"].dropna().astype(str).unique())
            selected_ids = st.multiselect(
                "Filter participants", participant_ids, default=participant_ids
            )
            filtered_live = live_df[live_df["participant_id"].astype(str).isin(selected_ids)]

        current_duration = duration_column(filtered_live)

        # Participant cards
        cards_df = filtered_live.head(24).copy()
        max_dur = 0
        if current_duration:
            cards_df[current_duration] = pd.to_numeric(cards_df[current_duration], errors="coerce")
            max_dur = cards_df[current_duration].max()
            if pd.isna(max_dur):
                max_dur = 0

        cols = st.columns(3)
        for i, (_, row) in enumerate(cards_df.iterrows()):
            pid = str(row.get("participant_id", f"#{i + 1}"))
            status = str(row.get("status", "Unknown")).title()
            initials = escape(pid[-2:].upper())

            bar_html = ""
            if current_duration and pd.notna(row.get(current_duration)):
                value = float(row[current_duration])
                pct = 0 if max_dur == 0 else min(100, value / max_dur * 100)
                bar_html = (
                    f'<div class="bar"><span style="width:{pct:.0f}%"></span></div>'
                    f'<div class="bar-meta"><span>Presence</span><span>{fmt_minutes(value)}</span></div>'
                )

            cols[i % 3].markdown(
                f'<div class="pcard"><div class="pcard-top">'
                f'<div class="avatar">{initials}</div>'
                f'<div style="flex:1"><div class="pname">{escape(pid)}</div>'
                f'<div class="psub">Tracked participant</div></div>'
                f'{pill(status, status_color(status))}</div>{bar_html}</div>',
                unsafe_allow_html=True,
            )

        section("Detailed Records")
        show_table(filtered_live)

        if current_duration:
            chart_data = filtered_live.copy()
            chart_data[current_duration] = pd.to_numeric(chart_data[current_duration], errors="coerce")

            if "participant_id" in chart_data.columns:
                fig = px.bar(
                    chart_data,
                    x="participant_id",
                    y=current_duration,
                    title="Presence Duration",
                    labels={"participant_id": "Participant", current_duration: "Seconds"},
                    color=current_duration,
                    color_continuous_scale=[VIOLET, CYAN],
                )
                fig.update_layout(coloraxis_showscale=False)
                fig.update_traces(marker_line_width=0)
                style_chart(fig)
                st.plotly_chart(fig, use_container_width=True)


# =========================================================
# SESSION HISTORY
# =========================================================

elif page == "Session History":
    section("Session History", "Browse, filter and export every saved session")

    if display_history.empty:
        empty_state("🗂️", "No history yet", "Run an attendance session to build your history.")

    else:
        history_view = display_history.copy()

        f1, f2 = st.columns(2)

        if "session_id" in history_view.columns:
            sessions = sorted(history_view["session_id"].dropna().astype(str).unique())
            selected_session = f1.selectbox("Select session", ["All Sessions"] + sessions)

            if selected_session != "All Sessions":
                history_view = history_view[history_view["session_id"].astype(str) == selected_session]

        if "participant_id" in history_view.columns:
            ids = sorted(history_view["participant_id"].dropna().astype(str).unique())
            selected_participants = f2.multiselect("Filter participants", ids, default=ids)
            history_view = history_view[
                history_view["participant_id"].astype(str).isin(selected_participants)
            ]

        kpi_row([
            ("Records", len(history_view), "in current view", "🧾", VIOLET),
            (
                "Sessions",
                int(history_view["session_id"].nunique()) if "session_id" in history_view.columns else 0,
                "in current view",
                "🎬",
                CYAN,
            ),
            (
                "Participants",
                int(history_view["participant_id"].nunique()) if "participant_id" in history_view.columns else 0,
                "unique tracking IDs",
                "👥",
                EMERALD,
            ),
        ])

        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
        show_table(history_view)

        st.download_button(
            "⬇  Download History CSV",
            data=history_view.to_csv(index=False).encode("utf-8"),
            file_name="attendance_history.csv",
            mime="text/csv",
        )

        if "session_id" in history_view.columns and not history_view.empty:
            counts = history_view.groupby("session_id").size().reset_index(name="Records")

            fig = px.bar(
                counts,
                x="session_id",
                y="Records",
                title="Records by Session",
                color="Records",
                color_continuous_scale=[VIOLET, CYAN],
            )
            fig.update_layout(coloraxis_showscale=False)
            fig.update_traces(marker_line_width=0)
            style_chart(fig)
            st.plotly_chart(fig, use_container_width=True)


# =========================================================
# ENGAGEMENT ANALYTICS
# =========================================================

elif page == "Engagement Analytics":
    section(
        "Engagement Analytics",
        "Presence duration is an activity measure, not a validated measure of attention or learning.",
    )

    analytics = display_history.copy()
    duration_col = duration_column(analytics)

    if using_demo:
        banner("The analytics below use illustrative demo records.", "info")

    if analytics.empty or not duration_col:
        empty_state("📉", "No duration data", "Suitable presence-duration records are not available yet.")

    else:
        analytics[duration_col] = pd.to_numeric(analytics[duration_col], errors="coerce")

        avg_all = analytics[duration_col].mean()
        peak = analytics[duration_col].max()
        present_rate = None
        if "status" in analytics.columns:
            present_rate = analytics["status"].astype(str).str.lower().eq("present").mean() * 100

        kpi_row([
            ("Avg Presence", fmt_minutes(avg_all), "per record", "⏱️", CYAN),
            ("Peak Presence", fmt_minutes(peak), "longest single record", "🚀", VIOLET),
            (
                "Present Rate",
                f"{present_rate:.0f}%" if present_rate is not None else "N/A",
                "records marked present",
                "🎯",
                EMERALD,
            ),
        ])

        # Heatmap
        if "participant_id" in analytics.columns and "session_id" in analytics.columns:
            section("Presence Heatmap", "Minutes present — participants × sessions")
            heat = analytics.pivot_table(
                index="participant_id",
                columns="session_id",
                values=duration_col,
                aggfunc="mean",
            ) / 60

            fig = px.imshow(
                heat,
                aspect="auto",
                color_continuous_scale=["#14122B", VIOLET, CYAN, EMERALD],
                labels=dict(x="Session", y="Participant", color="Minutes"),
            )
            fig.update_traces(xgap=4, ygap=4)
            style_chart(fig, 340)
            st.plotly_chart(fig, use_container_width=True)

        if "participant_id" in analytics.columns:
            if "session_id" in analytics.columns:
                summary = analytics.groupby("participant_id", as_index=False).agg(
                    Sessions=("session_id", "nunique"),
                    Average_Presence=(duration_col, "mean"),
                    Total_Records=(duration_col, "count"),
                )
            else:
                summary = analytics.groupby("participant_id", as_index=False).agg(
                    Average_Presence=(duration_col, "mean"),
                    Total_Records=(duration_col, "count"),
                )
                summary["Sessions"] = summary["Total_Records"]

            summary["Average_Presence"] = summary["Average_Presence"].round(1)

            c1, c2 = st.columns([1, 1.2])

            with c1:
                section("Participant Comparison")
                show_table(summary)

            with c2:
                section("Average Presence")
                fig = px.bar(
                    summary,
                    x="participant_id",
                    y="Average_Presence",
                    color="Sessions",
                    labels={
                        "participant_id": "Participant",
                        "Average_Presence": "Average Presence (seconds)",
                    },
                    color_continuous_scale=[VIOLET, CYAN],
                )
                fig.update_traces(marker_line_width=0)
                style_chart(fig, 330)
                st.plotly_chart(fig, use_container_width=True)

        if "session_id" in analytics.columns:
            trend = analytics.groupby("session_id", as_index=False)[duration_col].mean()

            fig = px.area(
                trend,
                x="session_id",
                y=duration_col,
                markers=True,
                title="Average Presence Across Sessions",
                labels={duration_col: "Seconds", "session_id": "Session"},
                color_discrete_sequence=[CYAN],
            )
            fig.update_traces(line=dict(width=3), fillcolor="rgba(45,212,191,0.16)")
            style_chart(fig)
            st.plotly_chart(fig, use_container_width=True)


# =========================================================
# INSTRUCTOR INSIGHTS
# =========================================================

elif page == "Instructor Insights":
    section(
        "Instructor Insights",
        "General teaching suggestions — not automatic conclusions about any student's mental state.",
    )

    tips = [
        ("🧠", "Check understanding", VIOLET,
         ["Ask a brief recap question after a difficult concept.",
          "Use a quick poll or short knowledge check."]),
        ("🙋", "Encourage participation", CYAN,
         ["Offer a pair discussion or a low-pressure question.",
          "Give students more than one way to participate."]),
        ("📋", "Review attendance", EMERALD,
         ["Look for repeated absences and follow up privately where appropriate.",
          "Check the context before drawing conclusions from attendance."]),
        ("⚖️", "Use evidence responsibly", AMBER,
         ["Face presence and duration do not prove attention or learning.",
          "Combine appropriate evidence with teacher judgement."]),
    ]

    for row_start in (0, 2):
        cols = st.columns(2)
        for col, (icon, title, tint, bullets) in zip(cols, tips[row_start:row_start + 2]):
            items = "".join(f"<li>{escape(b)}</li>" for b in bullets)
            col.markdown(
                f'<div class="icard" style="--tint:{tint}"><div class="icard-icon">{icon}</div>'
                f'<div class="icard-title">{escape(title)}</div><ul>{items}</ul></div>',
                unsafe_allow_html=True,
            )

    if "status" in display_history.columns:
        section("Attendance Status Summary")

        status_summary = (
            display_history["status"]
            .fillna("Unknown")
            .astype(str)
            .str.title()
            .value_counts()
            .rename_axis("Status")
            .reset_index(name="Records")
        )

        c1, c2 = st.columns([1, 1.3])
        with c1:
            show_table(status_summary)
        with c2:
            fig = px.bar(
                status_summary,
                x="Records",
                y="Status",
                orientation="h",
                color="Status",
                color_discrete_map=STATUS_COLORS,
            )
            fig.update_layout(showlegend=False)
            fig.update_traces(marker_line_width=0)
            style_chart(fig, 260)
            st.plotly_chart(fig, use_container_width=True)

    if using_demo:
        st.caption("Any historical figures shown here are illustrative demo data.")


# =========================================================
# STUDENT SUMMARY
# =========================================================

elif page == "Student Summary":
    section("Student Session Summary", "Pick a tracking ID to see its journey across sessions")

    if using_demo:
        banner("Demo mode: participant IDs and records below are illustrative.", "info")

    student_data = display_history.copy()

    if student_data.empty or "participant_id" not in student_data.columns:
        empty_state("🧑‍🎓", "No participant history", "Records appear once sessions have been saved.")

    else:
        student_ids = sorted(student_data["participant_id"].dropna().astype(str).unique())
        chosen_id = st.selectbox("Select Participant", student_ids)

        student_df = student_data[student_data["participant_id"].astype(str) == chosen_id].copy()

        total_sessions = (
            int(student_df["session_id"].nunique())
            if "session_id" in student_df.columns
            else len(student_df)
        )

        present_records = (
            int(student_df["status"].astype(str).str.lower().eq("present").sum())
            if "status" in student_df.columns
            else 0
        )

        duration_col = duration_column(student_df)

        average_duration = None
        if duration_col:
            student_df[duration_col] = pd.to_numeric(student_df[duration_col], errors="coerce")
            average_duration = student_df[duration_col].mean()

        st.markdown(
            f'<div class="pcard" style="padding:22px"><div class="pcard-top">'
            f'<div class="avatar" style="width:62px;height:62px;font-size:20px;border-radius:18px">'
            f'{escape(chosen_id[-2:].upper())}</div>'
            f'<div style="flex:1"><div class="pname" style="font-size:20px">{escape(chosen_id)}</div>'
            f'<div class="psub">{total_sessions} recorded session(s)</div></div>'
            f'{pill(f"{present_records} present", EMERALD)}</div></div>',
            unsafe_allow_html=True,
        )

        avg_text = (
            f"{average_duration:.0f} sec"
            if average_duration is not None and pd.notna(average_duration)
            else "N/A"
        )

        kpi_row([
            ("Recorded Sessions", total_sessions, "sessions attended", "🎬", VIOLET),
            ("Present Records", present_records, "marked present", "✅", EMERALD),
            ("Average Presence", avg_text, "per session", "⏱️", CYAN),
        ])

        section("Attendance Trend Across Sessions")

        if duration_col and "session_id" in student_df.columns:
            trend_df = student_df.groupby("session_id", as_index=False)[duration_col].mean()

            fig = px.area(
                trend_df,
                x="session_id",
                y=duration_col,
                markers=True,
                title=f"Recorded Presence Trend — {chosen_id}",
                labels={"session_id": "Session", duration_col: "Presence Duration (seconds)"},
                color_discrete_sequence=[VIOLET],
            )
            fig.update_traces(line=dict(width=3), fillcolor="rgba(99,102,241,0.18)")
            style_chart(fig)
            st.plotly_chart(fig, use_container_width=True)
        else:
            empty_state("📈", "Not enough data", "More sessions are needed to draw a trend.")

        section("Participant History")
        show_table(student_df)

        st.caption(
            "Tracking IDs are not verified identities and may be reused "
            "between separate camera sessions."
        )


# =========================================================
# FOOTER
# =========================================================

st.markdown(
    '<div class="foot">LearnMate • Classroom analytics prototype • '
    'Demo data is illustrative; live data depends on backend availability.</div>',
    unsafe_allow_html=True,
)