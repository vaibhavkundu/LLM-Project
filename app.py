import os
import tempfile
import streamlit as st

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

from resume_logic import extract_resume_text


# -----------------------------
# Page configuration
# -----------------------------
st.set_page_config(
    page_title="Resume Chatbot",
    layout="centered"
)

st.title("📄 Resume Chatbot")
st.write("Upload your resume (PDF or Word) and chat with it.")


# -----------------------------
# File uploader (PDF + DOCX)
# -----------------------------
uploaded_file = st.file_uploader(
    "Upload Resume (PDF or DOCX)",
    type=["pdf", "docx"]
)


if uploaded_file:
    # -----------------------------
    # Save uploaded file temporarily
    # -----------------------------
    file_name = uploaded_file.name.lower()

    if file_name.endswith(".pdf"):
        suffix = ".pdf"
    elif file_name.endswith(".docx"):
        suffix = ".docx"
    else:
        st.error("Unsupported file format")
        st.stop()

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.read())
        resume_path = tmp.name

    # -----------------------------
    # Extract resume text
    # -----------------------------
    try:
        resume_text = extract_resume_text(resume_path)
    except Exception as e:
        st.error("Failed to read resume file.")
        st.stop()

    if not resume_text.strip():
        st.error("Could not extract text from resume.")
        st.stop()

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
- Do NOT hallucinate or guess
- If something is not mentioned, clearly say "Not mentioned in the resume"
- Carefully calculate experience durations if asked

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
    # Chat input
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

        answer = response.content.strip()

        st.chat_message("assistant").markdown(answer)

        st.session_state.messages.append(
            {"role": "user", "content": user_input}
        )
        st.session_state.messages.append(
            {"role": "assistant", "content": answer}
        )
