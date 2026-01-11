import os
import uuid
import tempfile

import streamlit as st

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

from resume_logic import extract_resume_text
from analytics import log_resume_upload, log_chat


# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="Resume Chatbot",
    layout="centered"
)

st.title("📄 Resume Chatbot")
st.write("Upload your resume (PDF or Word) and chat with it.")


# =====================================================
# SESSION INITIALIZATION
# =====================================================
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "resume_uploaded" not in st.session_state:
    st.session_state.resume_uploaded = False

if "messages" not in st.session_state:
    st.session_state.messages = []


# =====================================================
# FILE UPLOAD (PDF / DOCX)
# =====================================================
uploaded_file = st.file_uploader(
    "Upload Resume (PDF or DOCX)",
    type=["pdf", "docx"]
)

if uploaded_file and not st.session_state.resume_uploaded:
    file_name = uploaded_file.name.lower()

    if file_name.endswith(".pdf"):
        suffix = ".pdf"
    elif file_name.endswith(".docx"):
        suffix = ".docx"
    else:
        st.error("Unsupported file format.")
        st.stop()

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.read())
        resume_path = tmp.name

    try:
        resume_text = extract_resume_text(resume_path)
    except Exception:
        st.error("Failed to extract text from resume.")
        st.stop()

    if not resume_text.strip():
        st.error("No readable text found in resume.")
        st.stop()

    st.session_state.resume_text = resume_text
    st.session_state.resume_uploaded = True

    # 🔥 LOG RESUME UPLOAD (SUPABASE)
    log_resume_upload(
        session_id=st.session_state.session_id,
        file_type=suffix
    )

    st.success("Resume uploaded successfully!")


# =====================================================
# CHATBOT (LLM ONLY)
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

RULES:
- Answer ONLY using the resume content below
- Do NOT hallucinate or guess
- If information is missing, say "Not mentioned in the resume"
- Calculate experience carefully if asked

Resume:
{context}

User Question:
{question}

Answer:
"""
    )

    # Show chat history
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

        # 🔥 LOG CHAT (SUPABASE)
        log_chat(
            session_id=st.session_state.session_id,
            user_msg=user_input,
            ai_msg=answer
        )
