from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()   #load .env

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

names = ["Gandalf", "Bilbo"]
sentences = ['By some curious chance one morning long ago in the quiet of the world, when there was less noise and more green, and the hobbits were still numerous and prosperous, and Bilbo Baggins was standing at his door after breakfast smoking an enormous long wooden pipe that reached nearly down to his wooly toes (neatly brushed) - Gandalf came by.', 'Gandalf sat at the head of the party with the thirteen dwarves all around: and Bilbo sat on a stool at the fire-side, nibbling at a biscuit (his appetite was quite taken away), and trying to look as if this was all perfectly ordinary and not in the least an adventure.']

sentences_text = " ".join(sentences)
names_text = ", ".join(names)

RELATION_SCHEMA = {
    "family":       ["parent_of", "sibling_of", "spouse_of", "ancestor_of"],
    "social":       ["friend_of", "enemy_of", "rival_of", "mentor_of", "lover_of", "admires"],
    "hierarchy":    ["ruler_of", "commands", "serves", "member_of_faction"],
    "action":       ["fights_against", "protects", "betrays", "saves", "hunts"],
    "knowledge":    ["knows_secret_of", "manipulates", "deceives"],
    "scifi_fantasy": ["creator_of", "clone_of"]
}

ALL_RELATIONS_STR = "\n".join(
    f"  [{cat}]: {', '.join(rels)}"
    for cat, rels in RELATION_SCHEMA.items()
)

prompt = f"""You are an expert in literary analysis of fantasy and science-fiction.

CHARACTERS:
{names_text}

TEXT FRAGMENT:
{sentences_text}

TASK:
Extract all relationships between the characters listed above.

ALLOWED RELATION TYPES (use ONLY these):
{ALL_RELATIONS_STR}

RULES:
- Use only relation types from the list above
- Relations must be supported by the text — either stated directly OR strongly implied by characters' actions and interactions
- Acceptable inference: characters sharing a meal, traveling together, or one giving orders to another
- Not acceptable: assuming relationship based on race, species, or role (e.g. "wizard therefore mentor")
- Direction: source → relation → target (e.g. "Gandalf mentor_of Frodo")
- Symmetric relations (friend_of, sibling_of, spouse_of, rival_of) — write once
- Directional relations (betrays, commands, protects, etc.) — source is the one performing the action
- If the same relation appears multiple times — include it once with the best evidence
- If no relation exists between two characters — do not invent one
- evidence must be a direct quote from the text

RETURN ONLY JSON, no text before or after:

{{
  "relations": [
    {{
      "source": "character name",
      "relation": "relation_type",
      "target": "character name",
      "evidence": "direct quote from the text"
    }}
  ]
}}"""

# response = client.chat.completions.create(
#     model="meta-llama/llama-3.1-8b-instruct",
#     messages=[
#         {"role": "system", "content": "Ekstrakcja relacji."},
#         {"role": "user", "content": prompt}
#     ],
# )
response = client.chat.completions.create(
    model="anthropic/claude-sonnet-4-6" ,
    messages=[
        {"role": "system", "content": "You are a literary analysis expert. Return only valid JSON."},
        {"role": "user", "content": prompt}
    ],
)
print(response.choices[0].message.content)