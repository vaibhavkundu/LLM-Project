import os
import uuid
import sqlite3
import tempfile
from datetime import datetime, date

import streamlit as st
import pandas as pd

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from resume_logic import extract_resume_text


# =====================================================
# DATABASE (SQLITE – STABLE)
# =====================================================
DB_PATH = "analytics.db"

def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            event_type TEXT,
            user_message TEXT,
            assistant_message TEXT,
            file_type TEXT,
            created_at TEXT
        )
    """)
    return conn

conn = get_db()

def log_event(event_type, session_id, user_msg=None, ai_msg=None, file_type=None):
    conn.execute(
        """
        INSERT INTO analytics
        (session_id, event_type, user_message, assistant_message, file_type, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            session_id,
            event_type,
            user_msg,
            ai_msg,
            file_type,
            datetime.utcnow().isoformat()
        )
    )
    conn.commit()


# =====================================================
# PAGE SETUP
# =====================================================
st.set_page_config(page_title="Resume Chatbot", layout="centered")
st.title("📄 Resume Chatbot")
st.write("Upload your resume (PDF or Word) and chat with it.")


# =====================================================
# SESSION STATE
# =====================================================
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "resume_uploaded" not in st.session_state:
    st.session_state.resume_uploaded = False

if "messages" not in st.session_state:
    st.session_state.messages = []


# =====================================================
# FILE UPLOAD
# =====================================================
uploaded_file = st.file_uploader(
    "Upload Resume (PDF or DOCX)",
    type=["pdf", "docx"]
)

if uploaded_file and not st.session_state.resume_uploaded:
    suffix = ".pdf" if uploaded_file.name.lower().endswith(".pdf") else ".docx"

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.read())
        resume_path = tmp.name

    resume_text = extract_resume_text(resume_path)
    st.session_state.resume_text = resume_text
    st.session_state.resume_uploaded = True

    log_event(
        event_type="resume_upload",
        session_id=st.session_state.session_id,
        file_type=suffix
    )

    st.success("Resume uploaded successfully!")


# =====================================================
# CHATBOT
# =====================================================
if st.session_state.get("resume_uploaded"):
    llm = ChatGroq(
        model="llama-3.1-8b-instant",
        temperature=0.2,
        api_key=os.environ.get("GROQ_API_KEY")
    )

    prompt = ChatPromptTemplate.from_template(
        """
You are a professional resume analysis assistant.

Rules:
- Answer ONLY using the resume content
- Do NOT hallucinate
- If information is missing, say "Not mentioned in the resume"

Resume:
{context}

Question:
{question}

Answer:
"""
    )

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).markdown(msg["content"])

    user_input = st.chat_input("Ask a question about the resume")

    if user_input:
        st.chat_message("user").markdown(user_input)

        response = llm.invoke(
            prompt.format_prompt(
                context=st.session_state.resume_text,
                question=user_input
            ).to_messages()
        )

        answer = response.content.strip()
        st.chat_message("assistant").markdown(answer)

        st.session_state.messages.extend([
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": answer}
        ])

        log_event(
            event_type="chat",
            session_id=st.session_state.session_id,
            user_msg=user_input,
            ai_msg=answer
        )


# =====================================================
# ADMIN ANALYTICS DASHBOARD (WORKING)
# =====================================================
st.sidebar.markdown("---")
admin = st.sidebar.checkbox("🔐 Admin Analytics")

if admin:
    st.sidebar.markdown("### 📊 Analytics")

    start_date = st.sidebar.date_input("Start date", date.today())
    end_date = st.sidebar.date_input("End date", date.today())

    df = pd.read_sql_query(
        """
        SELECT *
        FROM analytics
        WHERE DATE(created_at) BETWEEN ? AND ?
        ORDER BY created_at DESC
        """,
        conn,
        params=(start_date.isoformat(), end_date.isoformat())
    )

    st.sidebar.metric("Unique Users", df["session_id"].nunique())
    st.sidebar.metric("Total Chats", len(df[df["event_type"] == "chat"]))
    st.sidebar.metric("Resume Uploads", len(df[df["event_type"] == "resume_upload"]))

    st.sidebar.dataframe(df, use_container_width=True)

    csv = df.to_csv(index=False).encode("utf-8")
    st.sidebar.download_button(
        "⬇ Download CSV",
        csv,
        "analytics.csv",
        "text/csv"
    )
