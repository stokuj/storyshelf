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
sentences = ['By some curious chance one morning long ago in the quiet of the world, when there was less noise and more green, and the hobbits were still numerous and prosperous, and Bilbo Baggins was standing at his door after breakfast smoking an enormous long wooden pipe that reached nearly down to his wooly toes (neatly brushed) - Gandalf came by.', 'Gandalf sat at the head of the party with the thirteen dwarves all around: and Bilbo sat on a stool at the fire-side, nibbling at a biscuit (his appetite was quite taken away), and trying to look as if this was all perfectly ordinary and not in the least an adventure.', 'I have had enough to do washing up for fourteen!"\n\n"If you had dusted the mantelpiece, you would have found this under the clock," said Gandalf, handing Bilbo a note (written, of course, on his own note-paper).', 'Off you go!"\n\nTo the end of his days Bilbo could never remember how he found himself outside, without a hat, walking-stick, or any money, or anything that he usually took when he went out; leaving his second breakfast unfinished and quite unwashed-up, pushing the keys into Gandalf\'s hands, and running as fast as his furry feet could carry him down the lane, past the great Mill, across The Water, and then on for a whole mile or more.', 'Elrond gave Gandalf and Thorin each a sword; and Bilbo got a knife in a leather sheath.', 'That is why neither Bilbo, nor the dwarves, nor even Gandalf heard them coming.', 'Then he had questions of his own to ask, for if Gandalf had explained it all by now to the dwarves, Bilbo had not heard it.', 'The rest we all know - except that Gandalf knew all about the back-door, as the goblins called the lower gate, where Bilbo lost his buttons.', '"Can\'t help it," said Gandalf, "unless you like to go back and ask the goblins nicely to let you have your pony back and your luggage."\n\n"No, thank you!" said Bilbo.', 'I will tell you what Gandalf heard, though Bilbo did not understand it.', 'As Bilbo listened to the talk of Gandalf he realized that at last they were going to escape really and truly from the dreadful mountains.', 'Here they sat on wooden benches while Gandalf began his tale, and Bilbo swung his dangling legs and looked at the flowers in the garden, wondering what their names could be, as he had never seen half of them before.', '"Upon my word!" said Thorin, when Bilbo whispered to him to come out and join his friends, "Gandalf spoke true, as usual!', 'When Gandalf saw Bilbo, he was delighted.', "Anyway by mid-winter Gandalf and Bilbo had come all the way back, along both edges of the Forest, to the doors of Beorn's house; and there for a while they both stayed.", 'It was spring, and a fair one with mild weathers and a bright sun, before Bilbo and Gandalf took their leave at last of Beorn, and though he longed for home, Bilbo left with regret, for the flowers of the gardens of Beorn were in springtime no less marvellous than in high summer.']

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
#         {"role": "system", "content": "You are a literary analysis expert. Return only valid JSON."},
#         {"role": "user", "content": prompt}
#     ],
# )

# response = client.chat.completions.create(
#     model="anthropic/claude-sonnet-4-6" ,
#     messages=[
#         {"role": "system", "content": "You are a literary analysis expert. Return only valid JSON."},
#         {"role": "user", "content": prompt}
#     ],
# )

response = client.chat.completions.create(
    model="qwen/qwen3.5-flash-02-23",
    max_tokens=1000,
    messages=[
        {"role": "system", "content": "You are a literary analysis expert. Return only valid JSON."},
        {"role": "user", "content": prompt}
    ],
)

print(response.choices[0].message.content)