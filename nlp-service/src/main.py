"""Minimal NLP app using spaCy with file input support.

Run:
    python src/main.py
    python src/main.py --input ./book.txt
    python src/main.py --input ./book.epub
    python src/main.py --input ./book.pdf
"""

from __future__ import annotations

import argparse
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


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Extract book characters with spaCy")
    parser.add_argument("--input", help="Path to input file: .txt, .md, .epub, .pdf")
    parser.add_argument("--model", default="en_core_web_trf", help="spaCy model name")
    return parser.parse_args()


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


def main() -> None:
    args = parse_args()

    if args.input:
        try:
            text = load_text_from_file(args.input)
        except FileNotFoundError as error:
            print(str(error))
            return
        except ValueError as error:
            print(str(error))
            return
        except ModuleNotFoundError as error:
            missing = str(error).split("'")[1] if "'" in str(error) else str(error)
            print(f"Missing dependency: {missing}")
            print("Install project dependencies with: uv sync")
            return
    else:
        text = (
            "Alice met John in London. "
            "John told Alice about Emma. "
            "Later, Emma and Alice went for a walk."
        )

    selected_model = args.model
    try:
        characters = extract_characters(text, model_name=selected_model)
    except OSError:
        if selected_model == "en_core_web_trf":
            fallback_model = "en_core_web_sm"
            try:
                print(
                    "Model 'en_core_web_trf' not found, falling back to 'en_core_web_sm'."
                )
                characters = extract_characters(text, model_name=fallback_model)
                selected_model = fallback_model
            except OSError:
                print("Missing spaCy models: 'en_core_web_trf' and 'en_core_web_sm'.")
                print("Install one of them:")
                print("python -m spacy download en_core_web_trf")
                print("python -m spacy download en_core_web_sm")
                return
        else:
            print(f"Missing spaCy model '{selected_model}'.")
            print(f"Install model: python -m spacy download {selected_model}")
            return
    except ModuleNotFoundError:
        print("Missing spaCy package.")
        print("Install project dependencies with: uv sync")
        return

    print("Hello NLP!")
    print(f"Model: {selected_model}")
    print("Detected characters:")
    for name in characters:
        print(f"- {name}")


if __name__ == "__main__":
    main()
