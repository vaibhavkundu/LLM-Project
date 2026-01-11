import re
from langchain_community.document_loaders import Docx2txtLoader
from pypdf import PdfReader


def normalize_text(text: str) -> str:
    text = (
        text.replace("’", "'")
            .replace("‘", "'")
            .replace("–", "-")
            .replace("—", "-")
    )
    return text.strip()


def extract_text_from_docx(file_path: str) -> str:
    loader = Docx2txtLoader(file_path)
    docs = loader.load()
    text = "\n".join(d.page_content for d in docs)
    return normalize_text(text)


def extract_text_from_pdf(file_path: str) -> str:
    reader = PdfReader(file_path)
    pages = []
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            pages.append(page_text)
    return normalize_text("\n".join(pages))


def extract_resume_text(file_path: str) -> str:
    if file_path.lower().endswith(".docx"):
        return extract_text_from_docx(file_path)
    elif file_path.lower().endswith(".pdf"):
        return extract_text_from_pdf(file_path)
    else:
        raise ValueError("Unsupported file format. Upload PDF or DOCX only.")
