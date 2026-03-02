"""spaCy and input file helpers for character extraction."""

from __future__ import annotations

from pathlib import Path


def read_txt_file(file_path: Path) -> str:
    """Read plain text file with UTF-8 fallback handling."""
    try:
        return file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return file_path.read_text(encoding="utf-8-sig")


def read_epub_file(file_path: Path) -> str:
    """Extract visible text from an EPUB file."""
    from bs4 import BeautifulSoup
    from ebooklib import ITEM_DOCUMENT, epub

    book = epub.read_epub(str(file_path))
    parts: list[str] = []

    for item in book.get_items_of_type(ITEM_DOCUMENT):
        soup = BeautifulSoup(item.get_content(), "html.parser")
        text = soup.get_text(" ", strip=True)
        if text:
            parts.append(text)

    return "\n".join(parts)


def read_pdf_file(file_path: Path) -> str:
    """Extract text from a PDF file."""
    from pypdf import PdfReader

    reader = PdfReader(str(file_path))
    parts: list[str] = []

    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            parts.append(text)

    return "\n".join(parts)


def load_text_from_file(file_path: str) -> str:
    """Load raw book text from supported file formats."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    suffix = path.suffix.lower()
    if suffix in {".txt", ".md"}:
        return read_txt_file(path)
    if suffix == ".epub":
        return read_epub_file(path)
    if suffix == ".pdf":
        return read_pdf_file(path)

    raise ValueError("Unsupported format. Use: .txt, .md, .epub, .pdf")


def extract_characters(text: str, model_name: str = "en_core_web_sm") -> list[str]:
    """Return a unique list of characters detected as PERSON entities."""
    import spacy

    nlp = spacy.load(model_name)
    doc = nlp(text)
    characters = {
        ent.text.strip()
        for ent in doc.ents
        if ent.label_ == "persName" or ent.label_ == "PERSON"
    }
    return sorted(name for name in characters if name)
