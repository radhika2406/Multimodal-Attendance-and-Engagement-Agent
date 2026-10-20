
from pathlib import Path

import pandas as pd
import plotly.express as px
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


# =========================================================
# DEMO DATA
# =========================================================

def ensure_demo_data():
    """Create illustrative demo records without overwriting them."""
    if DEMO_CSV.exists():
        return

    rows = [
        ["DEMO-001", "P0001", "Present", 1780,
         "2026-10-16T09:00:00", "2026-10-16T09:30:00"],
        ["DEMO-001", "P0002", "Present", 1650,
         "2026-10-16T09:00:00", "2026-10-16T09:30:00"],
        ["DEMO-001", "P0003", "Pending", 420,
         "2026-10-16T09:00:00", "2026-10-16T09:30:00"],
        ["DEMO-001", "P0004", "Pending", 300,
         "2026-10-16T09:00:00", "2026-10-16T09:30:00"],
        ["DEMO-002", "P0001", "Present", 2100,
         "2026-10-18T10:00:00", "2026-10-18T10:35:00"],
        ["DEMO-002", "P0002", "Present", 1950,
         "2026-10-18T10:00:00", "2026-10-18T10:35:00"],
        ["DEMO-002", "P0003", "Present", 1600,
         "2026-10-18T10:00:00", "2026-10-18T10:35:00"],
        ["DEMO-002", "P0005", "Pending", 500,
         "2026-10-18T10:00:00", "2026-10-18T10:35:00"],
        ["DEMO-003", "P0001", "Present", 2400,
         "2026-10-19T11:00:00", "2026-10-19T11:40:00"],
        ["DEMO-003", "P0002", "Pending", 800,
         "2026-10-19T11:00:00", "2026-10-19T11:40:00"],
        ["DEMO-003", "P0004", "Present", 2200,
         "2026-10-19T11:00:00", "2026-10-19T11:40:00"],
        ["DEMO-003", "P0005", "Present", 2050,
         "2026-10-19T11:00:00", "2026-10-19T11:40:00"],
    ]

    columns = [
        "session_id",
        "participant_id",
        "status",
        "presence_duration_seconds",
        "session_started_at",
        "session_ended_at",
    ]

    pd.DataFrame(rows, columns=columns).to_csv(
        DEMO_CSV, index=False
    )


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
    response = requests.get(
        f"{API_URL}{path}", timeout=5
    )
    response.raise_for_status()
    return response.json()


def api_post(path):
    response = requests.post(
        f"{API_URL}{path}", timeout=10
    )
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


def style_chart(fig):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            family="Inter, sans-serif",
            color="#453760",
            size=12,
        ),
        margin=dict(t=45, b=20, l=15, r=15),
        legend_title_text="",
        xaxis=dict(
            gridcolor="#eee9f5",
            zerolinecolor="#e5def0",
            color="#625a78",
        ),
        yaxis=dict(
            gridcolor="#eee9f5",
            zerolinecolor="#e5def0",
            color="#625a78",
        ),
    )
    return fig


# =========================================================
# DESIGN — LAVENDER, WHITE AND PURPLE
# =========================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --ink: #30294b;
    --muted: #77728b;
    --purple: #514078;
    --lavender: #eeeafa;
    --line: #e8e4f1;
    --panel: #ffffff;
}

html, body, [class*="css"] {
    font-family: Inter, sans-serif;
}

.stApp {
    background: linear-gradient(
        135deg,
        #f3f0fa 0%,
        #f8f7fc 48%,
        #eeebf7 100%
    );
    color: var(--ink);
}

[data-testid="stHeader"] {
    background: rgba(248, 247, 252, .88);
}

[data-testid="stMainBlockContainer"] {
    padding-top: 1.4rem;
    padding-bottom: 2rem;
}

[data-testid="stSidebar"] {
    background: linear-gradient(
        180deg,
        #342752 0%,
        #443568 62%,
        #514078 100%
    );
    border-right: none;
}

[data-testid="stSidebar"] * {
    color: #f8f6ff;
}

[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
    color: #d6cfea;
}

[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,.18);
}

[data-testid="stSidebar"] [role="radiogroup"] {
    gap: .25rem;
}

[data-testid="stSidebar"] [role="radiogroup"] label {
    border-radius: 11px;
    padding: .48rem .65rem;
    transition: background .15s ease;
}

[data-testid="stSidebar"] [role="radiogroup"] label:hover {
    background: rgba(255,255,255,.12);
}

[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
    background: #f4f1fc;
    color: #443568;
}

[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) * {
    color: #443568;
}

h1, h2, h3, h4 {
    color: #30294b;
    letter-spacing: -.35px;
}

p, label, [data-testid="stCaptionContainer"] {
    color: var(--muted);
}

[data-testid="stMarkdownContainer"] a {
    color: #6552a0;
}

[data-testid="stMetric"] {
    background: #fff;
    border: 1px solid #e8e2f2;
    border-left: 4px solid #a99ad4;
    padding: 17px 18px;
    border-radius: 15px;
    box-shadow: 0 5px 18px rgba(60, 43, 96, .055);
}

[data-testid="stHorizontalBlock"] [data-testid="stMetric"] {
    min-height: 112px;
}

[data-testid="stMetricLabel"] {
    color: #77728b;
    font-weight: 600;
}

[data-testid="stMetricValue"] {
    color: #342752;
    font-weight: 750;
}

[data-testid="stMetricDelta"] {
    font-size: .8rem;
}

.stButton > button,
[data-testid="stDownloadButton"] button {
    min-height: 41px;
    border-radius: 11px;
    border: 1px solid #66539a;
    background: linear-gradient(110deg, #514078, #7160a7);
    color: #fff;
    font-weight: 650;
    box-shadow: 0 3px 9px rgba(81, 64, 120, .12);
}

.stButton > button:hover,
[data-testid="stDownloadButton"] button:hover {
    border-color: #8978bb;
    background: #433361;
    color: #fff;
}

.stButton > button:focus {
    box-shadow: 0 0 0 .18rem rgba(113,96,167,.25);
}

.hero {
    padding: 27px 30px;
    background: linear-gradient(115deg, #ffffff 0%, #f5f2fc 100%);
    border: 1px solid #e5def2;
    border-left: 5px solid #8d7abb;
    border-radius: 19px;
    margin-bottom: 22px;
    box-shadow: 0 8px 25px rgba(62, 47, 96, .06);
}

.eyebrow {
    color: #7966a9;
    text-transform: uppercase;
    font-size: 11px;
    letter-spacing: 2px;
    font-weight: 800;
}

.hero-title {
    font-size: 31px;
    font-weight: 800;
    color: #30294b;
    margin-top: 5px;
}

.hero-sub {
    color: #77728b;
    margin-top: 8px;
}

.panel {
    background: #fff;
    border: 1px solid #e8e2f2;
    border-radius: 15px;
    padding: 18px;
    box-shadow: 0 5px 18px rgba(60,43,96,.045);
}

.muted {
    color: #77728b;
    font-size: 13px;
}

hr {
    border-color: #e8e2f2;
}

[data-testid="stDataFrame"],
[data-testid="stTable"] {
    border: 1px solid #e8e2f2;
    border-radius: 12px;
    overflow: hidden;
}

[data-testid="stDataFrame"] [role="columnheader"] {
    background: #f1edf9;
    color: #453760;
}

[data-testid="stAlert"] {
    border-radius: 12px;
}

[data-testid="stPlotlyChart"] {
    background: #fff;
    border: 1px solid #ebe6f3;
    border-radius: 15px;
    padding: 8px;
    box-shadow: 0 4px 16px rgba(60,43,96,.035);
}

[data-baseweb="select"] > div,
[data-baseweb="input"] > div,
[data-baseweb="textarea"] > div {
    border-radius: 10px;
    border-color: #ded7ec;
}

@media (max-width: 760px) {
    .hero {
        padding: 21px 20px;
    }

    .hero-title {
        font-size: 25px;
    }
}
</style>
""", unsafe_allow_html=True)


# =========================================================
# SIDEBAR AND SESSION CONTROLS
# =========================================================

with st.sidebar:
    st.markdown("## 🎓 LearnMate")
    st.caption("AI CLASSROOM INTELLIGENCE")
    st.divider()

    page = st.radio(
        "NAVIGATION",
        [
            "Overview",
            "Live Attendance",
            "Session History",
            "Engagement Analytics",
            "Instructor Insights",
            "Student Summary",
        ],
    )

    st.divider()
    st.markdown("### SESSION CONTROL")

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


# =========================================================
# LOAD DATA
# =========================================================

real_history = load_real_history()
demo_history = load_demo_history()

# Keep illustrative demo data separate from real attendance.
using_demo = real_history.empty

if using_demo:
    display_history = demo_history.copy()
else:
    display_history = real_history.copy()

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
# PAGE HEADER
# =========================================================

st.markdown("""
<div class="hero">
    <div class="eyebrow">CLASSROOM INTELLIGENCE PLATFORM</div>
    <div class="hero-title">Your classroom, in focus.</div>
    <div class="hero-sub">
        Attendance operations, session history, and teaching insights
        in one workspace.
    </div>
</div>
""", unsafe_allow_html=True)

if using_demo:
    st.info(
        "Demo mode: illustrative records are displayed because no real "
        "attendance history has been saved yet. Demo records are not real "
        "student attendance."
    )


# =========================================================
# OVERVIEW
# =========================================================

if page == "Overview":
    st.subheader("Classroom Overview")

    present_count = 0
    if "status" in live_df.columns:
        present_count = int(
            live_df["status"].astype(str).str.lower().eq("present").sum()
        )

    record_count = len(display_history)

    session_count = (
        display_history["session_id"].nunique()
        if "session_id" in display_history.columns
        else 0
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Live Participants", len(live_df))
    c2.metric("Marked Present", present_count)
    c3.metric("Historical Records", record_count)
    c4.metric("Sessions Recorded", int(session_count))

    st.divider()

    left, right = st.columns([1.25, 1])

    with left:
        st.subheader("Current Attendance")

        if not live_df.empty:
            st.dataframe(
                live_df,
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info(
                "No live records currently available. Start attendance "
                "and keep a face visible."
            )

    with right:
        st.subheader("Attendance Status")

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
                .value_counts()
                .rename_axis("Status")
                .reset_index(name="Records")
            )

            fig = px.pie(
                status_data,
                names="Status",
                values="Records",
                hole=0.66,
                color_discrete_sequence=[
                    "#7562A6",
                    "#F2C94C",
                    "#53B77A",
                    "#E99595",
                ],
            )
            fig.update_traces(
                textposition="inside",
                textinfo="label+percent",
            )
            style_chart(fig)
            st.plotly_chart(fig, use_container_width=True)

            if chart_is_demo:
                st.caption("Illustrative demo attendance distribution.")
        else:
            st.info("Attendance status will appear when records exist.")

    st.subheader("Recent Attendance History")
    st.dataframe(
        display_history.tail(10),
        use_container_width=True,
        hide_index=True,
    )


# =========================================================
# LIVE ATTENDANCE
# =========================================================

elif page == "Live Attendance":
    st.subheader("Live Attendance")
    st.write(
        "Use the sidebar to start or stop the session. Refresh to fetch "
        "the latest records from FastAPI."
    )

    if not backend_ok:
        st.error("Backend is unavailable. Start FastAPI first.")
        if backend_error:
            st.caption(backend_error)

    elif live_df.empty:
        st.info(
            "No current participant records. Start a session, keep your "
            "face visible, and refresh this page."
        )

    else:
        if "participant_id" in live_df.columns:
            participant_ids = sorted(
                live_df["participant_id"].dropna().astype(str).unique()
            )
            selected_ids = st.multiselect(
                "Filter participants",
                participant_ids,
                default=participant_ids,
            )
            filtered_live = live_df[
                live_df["participant_id"].astype(str).isin(selected_ids)
            ]
        else:
            filtered_live = live_df

        st.dataframe(
            filtered_live,
            use_container_width=True,
            hide_index=True,
        )

        current_duration = duration_column(filtered_live)

        if current_duration:
            chart_data = filtered_live.copy()
            chart_data[current_duration] = pd.to_numeric(
                chart_data[current_duration],
                errors="coerce",
            )

            if "participant_id" in chart_data.columns:
                chart_data = chart_data.set_index("participant_id")

            st.subheader("Presence Duration")
            st.bar_chart(chart_data[[current_duration]])


# =========================================================
# SESSION HISTORY
# =========================================================

elif page == "Session History":
    st.subheader("Session History")

    if using_demo:
        st.info("Showing illustrative demo history.")

    if display_history.empty:
        st.info("No history is available yet.")

    else:
        history_view = display_history.copy()

        if "session_id" in history_view.columns:
            sessions = sorted(
                history_view["session_id"].dropna().astype(str).unique()
            )
            selected_session = st.selectbox(
                "Select session",
                ["All Sessions"] + sessions,
            )

            if selected_session != "All Sessions":
                history_view = history_view[
                    history_view["session_id"].astype(str) == selected_session
                ]

        if "participant_id" in history_view.columns:
            ids = sorted(
                history_view["participant_id"].dropna().astype(str).unique()
            )
            selected_participants = st.multiselect(
                "Filter participants",
                ids,
                default=ids,
            )
            history_view = history_view[
                history_view["participant_id"].astype(str).isin(
                    selected_participants
                )
            ]

        st.dataframe(
            history_view,
            use_container_width=True,
            hide_index=True,
        )

        st.download_button(
            "Download History CSV",
            data=history_view.to_csv(index=False).encode("utf-8"),
            file_name="attendance_history.csv",
            mime="text/csv",
        )

        if "session_id" in history_view.columns:
            counts = (
                history_view.groupby("session_id")
                .size()
                .reset_index(name="Records")
            )

            fig = px.bar(
                counts,
                x="session_id",
                y="Records",
                title="Records by Session",
                color_discrete_sequence=["#8D7ABB"],
            )
            style_chart(fig)
            st.plotly_chart(fig, use_container_width=True)


# =========================================================
# ENGAGEMENT ANALYTICS
# =========================================================

elif page == "Engagement Analytics":
    st.subheader("Engagement Analytics")

    st.caption(
        "Presence duration is an activity measure, not a validated "
        "measure of attention or learning."
    )

    analytics = display_history.copy()
    duration_col = duration_column(analytics)

    if using_demo:
        st.info("The analytics below use illustrative demo records.")

    if analytics.empty or not duration_col:
        st.info("No suitable duration data is available.")

    else:
        analytics[duration_col] = pd.to_numeric(
            analytics[duration_col],
            errors="coerce",
        )

        if "participant_id" in analytics.columns:
            if "session_id" in analytics.columns:
                summary = (
                    analytics.groupby("participant_id", as_index=False)
                    .agg(
                        Sessions=("session_id", "nunique"),
                        Average_Presence=(duration_col, "mean"),
                        Total_Records=(duration_col, "count"),
                    )
                )
            else:
                summary = (
                    analytics.groupby("participant_id", as_index=False)
                    .agg(
                        Average_Presence=(duration_col, "mean"),
                        Total_Records=(duration_col, "count"),
                    )
                )
                summary["Sessions"] = summary["Total_Records"]

            summary["Average_Presence"] = (
                summary["Average_Presence"].round(1)
            )

            st.subheader("Participant Comparison")
            st.dataframe(
                summary,
                use_container_width=True,
                hide_index=True,
            )

            fig = px.bar(
                summary,
                x="participant_id",
                y="Average_Presence",
                color="Sessions",
                title="Average Recorded Presence by Participant",
                labels={
                    "participant_id": "Participant",
                    "Average_Presence": "Average Presence (seconds)",
                    "Sessions": "Sessions",
                },
                color_continuous_scale=["#B8AED9", "#65528F"],
            )
            style_chart(fig)
            st.plotly_chart(fig, use_container_width=True)

        if (
            "session_id" in analytics.columns
            and not analytics.empty
        ):
            trend = (
                analytics.groupby("session_id", as_index=False)[duration_col]
                .mean()
            )

            fig = px.line(
                trend,
                x="session_id",
                y=duration_col,
                markers=True,
                title="Average Presence Across Sessions",
                color_discrete_sequence=["#53B77A"],
            )
            style_chart(fig)
            st.plotly_chart(fig, use_container_width=True)


# =========================================================
# INSTRUCTOR INSIGHTS
# =========================================================

elif page == "Instructor Insights":
    st.subheader("Instructor Insights")

    st.write(
        "These are general teaching suggestions. They are not automatic "
        "conclusions about any student's mental state."
    )

    st.markdown("### Suggested Teaching Actions")

    st.markdown("""
**Check understanding**
- Ask a brief recap question after a difficult concept.
- Use a quick poll or short knowledge check.

**Encourage participation**
- Offer a pair discussion or a low-pressure question.
- Give students more than one way to participate.

**Review attendance**
- Look for repeated absences and follow up privately where appropriate.
- Check the context before drawing conclusions from attendance.

**Use evidence responsibly**
- Face presence and duration do not prove attention or learning.
- Combine appropriate evidence with teacher judgement.
""")

    if "status" in display_history.columns:
        st.subheader("Attendance Status Summary")
        status_summary = (
            display_history["status"]
            .fillna("Unknown")
            .value_counts()
            .rename_axis("Status")
            .reset_index(name="Records")
        )
        st.dataframe(
            status_summary,
            use_container_width=True,
            hide_index=True,
        )

    if using_demo:
        st.caption(
            "Any historical figures shown here are illustrative demo data."
        )


# =========================================================
# STUDENT SUMMARY
# =========================================================

elif page == "Student Summary":
    st.subheader("Student Session Summary")

    if using_demo:
        st.info(
            "Demo mode: participant IDs and records below are illustrative."
        )

    student_data = display_history.copy()

    if student_data.empty or "participant_id" not in student_data.columns:
        st.info("No participant history is available.")

    else:
        student_ids = sorted(
            student_data["participant_id"].dropna().astype(str).unique()
        )

        chosen_id = st.selectbox(
            "Select Participant",
            student_ids,
        )

        student_df = student_data[
            student_data["participant_id"].astype(str) == chosen_id
        ].copy()

        total_sessions = (
            student_df["session_id"].nunique()
            if "session_id" in student_df.columns
            else len(student_df)
        )

        present_records = (
            int(
                student_df["status"]
                .astype(str)
                .str.lower()
                .eq("present")
                .sum()
            )
            if "status" in student_df.columns
            else 0
        )

        duration_col = duration_column(student_df)

        average_duration = None
        if duration_col:
            student_df[duration_col] = pd.to_numeric(
                student_df[duration_col],
                errors="coerce",
            )
            average_duration = student_df[duration_col].mean()

        a, b, c = st.columns(3)
        a.metric("Recorded Sessions", total_sessions)
        b.metric("Present Records", present_records)

        if average_duration is not None and pd.notna(average_duration):
            c.metric("Average Presence", f"{average_duration:.0f} sec")
        else:
            c.metric("Average Presence", "N/A")

        st.subheader("Attendance Trend Across Sessions")

        if duration_col and "session_id" in student_df.columns:
            trend_df = (
                student_df.groupby("session_id", as_index=False)[duration_col]
                .mean()
            )

            fig = px.line(
                trend_df,
                x="session_id",
                y=duration_col,
                markers=True,
                title=f"Recorded Presence Trend — {chosen_id}",
                labels={
                    "session_id": "Session",
                    duration_col: "Presence Duration (seconds)",
                },
                color_discrete_sequence=["#7562A6"],
            )
            style_chart(fig)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Not enough session data to create a trend.")

        st.subheader("Participant History")
        st.dataframe(
            student_df,
            use_container_width=True,
            hide_index=True,
        )

        st.caption(
            "Tracking IDs are not verified identities and may be reused "
            "between separate camera sessions."
        )


# =========================================================
# FOOTER
# =========================================================

st.divider()
st.caption(
    "LearnMate • Classroom analytics prototype • "
    "Demo data is illustrative; live data depends on backend availability."
)
