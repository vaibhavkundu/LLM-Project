import re
from langchain_community.document_loaders import Docx2txtLoader


def extract_resume_text(file_path: str) -> str:
    loader = Docx2txtLoader(file_path)
    docs = loader.load()
    text = "\n".join(d.page_content for d in docs)

    # normalize quotes & dashes
    text = (
        text.replace("’", "'")
            .replace("‘", "'")
            .replace("–", "-")
            .replace("—", "-")
    )

    return text.strip()
