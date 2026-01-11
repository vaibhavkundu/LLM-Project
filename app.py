import os
import tempfile
import streamlit as st

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

from resume_logic import extract_resume_text


# -----------------------------
# Page setup
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
    st.success("Resume uploaded successfully!")

    # -----------------------------
    # Initialize Groq LLM
    # -----------------------------
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
- Do NOT guess or hallucinate
- If information is missing, say "Not mentioned in the resume"
- Calculate experience durations carefully when asked

Resume:
{context}

User Question:
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
