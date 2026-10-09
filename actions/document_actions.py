"""
Reads and extracts text from documents (PDF, Word, RTF, plain text) so the
assistant can summarize or answer questions about them. The extracted text
is returned to the LLM as a tool result, which then summarizes it in its
own reply — this module doesn't do the summarizing itself.
"""
import subprocess
import os

MAX_CHARS = 6000  # keep the extracted text reasonably sized for the model


def read_document(path: str) -> str:
    """Extracts text from a document (PDF, DOCX, DOC, RTF, TXT, etc).
    Returns a truncated excerpt if the document is long."""
    path = os.path.expanduser(path)
    if not os.path.isfile(path):
        return f"File not found: {path}"

    ext = os.path.splitext(path)[1].lower()
    try:
        if ext == ".pdf":
            text = _read_pdf(path)
        else:
            # textutil is built into macOS and handles docx, doc, rtf, rtfd, txt, html...
            result = subprocess.run(
                ["textutil", "-convert", "txt", "-stdout", path],
                capture_output=True, text=True,
            )
            text = result.stdout
    except Exception as e:
        return f"Couldn't read the file: {e}"

    text = text.strip()
    if not text:
        return "The document appears to be empty or couldn't be read."
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS] + "... [truncated]"
    return text


def _read_pdf(path: str) -> str:
    from PyPDF2 import PdfReader
    reader = PdfReader(path)
    pages_text = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages_text)
