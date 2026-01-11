import streamlit as st
import tempfile

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

from resume_logic import (
    extract_resume_text,
    extract_experience,
    total_experience_months,
    format_ym
)

# -----------------------------
# Page config
# -----------------------------
st.set_page_config(page_title="Resume Chatbot", layout="centered")
st.title("📄 Resume Chatbot")

st.write("Upload your resume and chat with it")

# -----------------------------
# Upload resume
# -----------------------------
uploaded_file = st.file_uploader("Upload Resume (.docx)", type=["docx"])

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
        tmp.write(uploaded_file.read())
        resume_path = tmp.name

    resume_text = extract_resume_text(resume_path)
    experiences = extract_experience(resume_text)
    total_months = total_experience_months(experiences)

    st.success("Resume processed successfully!")

    # -----------------------------
    # Initialize LLM
    # -----------------------------
    llm = ChatGroq(
        model="llama-3.1-8b-instant",
        temperature=0.2
    )

    prompt = ChatPromptTemplate.from_template(
        """
You are a professional resume analysis assistant.

Answer ONLY using the resume content below.
If information is not present, say so clearly.

Resume:
{context}

Question:
{question}

Answer:
"""
    )

    # -----------------------------
    # Chat history
    # -----------------------------
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).markdown(msg["content"])

    # -----------------------------
    # User input
    # -----------------------------
    user_input = st.chat_input("Ask a question about the resume")

    if user_input:
        st.chat_message("user").markdown(user_input)

        q = user_input.lower()

        # Deterministic experience answer
        if "experience" in q or "month" in q or "year" in q:
            answer = f"Total professional experience is {format_ym(total_months)}."
        else:
            response = llm.invoke(
                prompt.format_prompt(
                    context=resume_text,
                    question=user_input
                ).to_messages()
            )
            answer = response.content

        st.chat_message("assistant").markdown(answer)

        st.session_state.messages.append({"role": "user", "content": user_input})
        st.session_state.messages.append({"role": "assistant", "content": answer})

