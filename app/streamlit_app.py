from __future__ import annotations

import io
import os
import sys
from datetime import UTC, datetime

import pandas as pd
import streamlit as st

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from sql_agent.agent import SQLAgent
from sql_agent.config import Settings


st.set_page_config(
    page_title="LLM-Powered SQL Agent",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
    .main-header {
        background: linear-gradient(90deg, #083d77 0%, #0f6ba8 100%);
        padding: 0.9rem 1.2rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 1rem;
    }
    .hint-box {
        background-color: #eef6fb;
        border-left: 4px solid #0f6ba8;
        padding: 0.8rem;
        border-radius: 6px;
        margin: 0.4rem 0 0.8rem 0;
    }
</style>
""",
    unsafe_allow_html=True,
)

if "history" not in st.session_state:
    st.session_state.history = []
if "generated_sql" not in st.session_state:
    st.session_state.generated_sql = ""
if "last_question" not in st.session_state:
    st.session_state.last_question = ""
if "last_df" not in st.session_state:
    st.session_state.last_df = pd.DataFrame()
if "quick_questions" not in st.session_state:
    st.session_state.quick_questions = []
if "quick_questions_key" not in st.session_state:
    st.session_state.quick_questions_key = ""

settings = Settings.from_env()

st.markdown(
    """
<div class='main-header'>
    <h2 style='margin: 0;'>SQL Agent for BI Analysis</h2>
    <p style='margin: 0.3rem 0 0 0;'>Ask business questions, generate SQL, review results, and get AI insights.</p>
</div>
""",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Configuration")

    st.caption("Database Engine: MS SQL SERVER")
    settings.db_name = st.text_input("Database", value=settings.db_name)
    settings.db_table = st.text_input("Table", value=settings.db_table)
    settings.llm_model = st.text_input("Gemini Model", value=settings.llm_model)

    if settings.gemini_api_key:
        st.success("GEMINI_API_KEY detected from environment")
    else:
        st.warning("GEMINI_API_KEY not found in environment")

question = st.text_input(
    "Ask your business question",
    value=st.session_state.last_question,
    placeholder="Example: What are the top 10 states by number of customers?",
)

st.markdown("<div class='hint-box'>Tip: You can generate SQL first, edit it manually, then execute.</div>", unsafe_allow_html=True)

col_a, col_b, col_c = st.columns([1, 1, 2])
with col_a:
    generate_btn = st.button("1) Generate SQL", width="stretch")
with col_b:
    execute_btn = st.button("2) Execute SQL", width="stretch")

agent = None
agent_error = None
try:
    agent = SQLAgent(settings=settings)
except Exception as ex:
    agent_error = str(ex)


def get_quick_questions(force_refresh: bool = False) -> list[str]:
    fallback_questions = [
        "What is the total number of records?",
        "What are the top 10 categories by count?",
        "How are values distributed by the main status column?",
        "Which segment has the highest average value?",
    ]

    if not agent:
        return fallback_questions

    key = f"{settings.db_name}|{settings.db_schema}|{settings.db_table}|{settings.llm_model}"
    if (not force_refresh) and st.session_state.quick_questions and st.session_state.quick_questions_key == key:
        return st.session_state.quick_questions

    try:
        metadata = agent.get_metadata()
        suggestions = agent.suggest_quick_questions(metadata=metadata, limit=4)
        final_questions = suggestions if suggestions else fallback_questions
    except Exception:
        final_questions = fallback_questions

    st.session_state.quick_questions = final_questions
    st.session_state.quick_questions_key = key
    return final_questions

if agent_error:
    st.error(f"Initialization error: {agent_error}")

with st.sidebar:
    st.markdown("---")
    st.subheader("Quick Questions")
    refresh_suggestions = st.button("Refresh Suggestions", width="stretch")
    dynamic_questions = get_quick_questions(force_refresh=refresh_suggestions)
    for sample in dynamic_questions:
        if st.button(sample, width="stretch"):
            st.session_state.last_question = sample

if generate_btn and question and agent:
    try:
        metadata = agent.get_metadata()
        st.session_state.generated_sql = agent.generate_sql(question, metadata)
        st.success("SQL generated successfully.")
    except Exception as ex:
        st.error(f"Failed to generate SQL: {ex}")

st.session_state.generated_sql = st.text_area(
    "Generated SQL (editable)",
    value=st.session_state.generated_sql,
    height=180,
)

if execute_btn and st.session_state.generated_sql.strip() and question and agent:
    try:
        df = agent.run_sql(st.session_state.generated_sql)
        st.session_state.last_df = df

        st.subheader("Query Results")
        st.dataframe(df, width="stretch")

        if df.empty:
            answer = "No rows returned by the SQL query."
        else:
            # Limit rows sent to LLM so insights remain reliable and fast.
            insight_df = df.head(200)
            try:
                answer = agent.answer_from_df(question, insight_df)
                if not answer or not answer.strip():
                    answer = "Insight generation returned an empty response. Please re-run or refine the question."
            except Exception as insight_ex:
                answer = (
                    "Insight generation failed, but query results are available. "
                    f"Details: {insight_ex}"
                )

        st.subheader("AI Insight")
        st.write(answer)

        st.session_state.history.append(
            {
                "timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
                "question": question,
                "sql": st.session_state.generated_sql,
                "rows": int(len(df)),
            }
        )

    except Exception as ex:
        st.error(f"Execution failed: {ex}")

if not st.session_state.last_df.empty:
    st.subheader("Quick Chart")
    chart_df = st.session_state.last_df.copy()
    numeric_cols = [c for c in chart_df.columns if pd.api.types.is_numeric_dtype(chart_df[c])]

    if numeric_cols and len(chart_df.columns) >= 2:
        x_col = st.selectbox("X axis", options=chart_df.columns, index=0)
        y_col = st.selectbox("Y axis", options=numeric_cols, index=0)
        chart_type = st.radio("Chart type", options=["Bar", "Line"], horizontal=True)

        if chart_type == "Bar":
            st.bar_chart(chart_df.set_index(x_col)[y_col])
        else:
            st.line_chart(chart_df.set_index(x_col)[y_col])
    else:
        st.info("Need at least one numeric column to plot a chart.")

st.markdown("---")
st.subheader("Query History")
if st.session_state.history:
    hist_df = pd.DataFrame(st.session_state.history)
    st.dataframe(hist_df, width="stretch")

    csv_buffer = io.StringIO()
    hist_df.to_csv(csv_buffer, index=False)
    st.download_button(
        "Download History CSV",
        data=csv_buffer.getvalue(),
        file_name="sql_agent_history.csv",
        mime="text/csv",
    )
else:
    st.info("No queries executed yet.")
