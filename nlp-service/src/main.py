"""CLI entrypoint for character extraction with spaCy.

Run:
    python -m src.main
    python -m src.main --input ./book.txt
    python -m src.main --input ./book.epub
    python -m src.main --input ./book.pdf
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    script_dir = Path(__file__).resolve().parent
    root_dir = script_dir.parent
    if str(script_dir) in sys.path:
        sys.path.remove(str(script_dir))
    sys.path.insert(0, str(root_dir))

from src.spacy import extract_characters, load_text_from_file


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Extract book characters with spaCy")
    parser.add_argument("--input", help="Path to input file: .txt, .md, .epub, .pdf")
    parser.add_argument("--model", default="en_core_web_trf", help="spaCy model name")
    return parser.parse_args()


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
