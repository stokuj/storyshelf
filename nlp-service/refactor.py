import os
import glob

replacements = {
    # Clients and Core
    "api.services.callback_client": "api.services.clients.spring_client",
    "api.services.transformers_service": "api.services.core.transformers_engine",
    "api.services.llm_service": "api.services.core.llm_engine",
    # Book service split
    "api.services.book_service import analyse_text": "api.services.core.text_stats import analyse_text",
    "api.services.book_service import find_sentences_with_both_characters": "api.services.core.text_parser import find_sentences_with_both_characters",
    "api.services.book_service": "api.services.core.text_parser",  # fallback
    # Workflows
    "api.services.analyse_service": "api.services",
    "api.services.ner_service": "api.services",
    "api.services.find_pairs_service": "api.services",
    "api.services.relations_service": "api.services",
}


def process_file(filepath):
    with open(filepath, "r") as f:
        content = f.read()

    new_content = content
    for old, new in replacements.items():
        new_content = new_content.replace(old, new)

    if content != new_content:
        print(f"Updated {filepath}")
        with open(filepath, "w") as f:
            f.write(new_content)


for filepath in glob.glob("api/**/*.py", recursive=True):
    process_file(filepath)

for filepath in glob.glob("test/**/*.py", recursive=True):
    process_file(filepath)
