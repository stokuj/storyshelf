from openai import OpenAI
import os

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

prompt = """
Masz listę postaci:
[Gandalf, Bilbo]

Analizuj fragment tekstu-zdań:
['By some curious chance one morning long ago in the quiet of the world, when there was less noise and more green, and the hobbits were still numerous and prosperous, and Bilbo Baggins was standing at his door after breakfast smoking an enormous long wooden pipe that reached nearly down to his wooly toes (neatly brushed) - Gandalf came by.', 'Gandalf sat at the head of the party with the thirteen dwarves all around: and Bilbo sat on a stool at the fire-side, nibbling at a biscuit (his appetite was quite taken away), and trying to look as if this was all perfectly ordinary and not in the least an adventure.']

Wyciągnij:

1. Relacje między postaciami
2. Typ relacji
3. Kierunek
4. Kontekst (zdanie jako dowód)

Zwróć tylko JSON w formacie:

{
  "relations": [
    {
      "source": "",
      "relation": "",
      "target": "",
      "evidence": ""
    }
  ]
}
"""

response = client.chat.completions.create(
    model="meta-llama/llama-3.1-8b-instruct",
    messages=[
        {"role": "system", "content": "Ekstrakcja relacji."},
        {"role": "user", "content": prompt}
    ],
)

print(response.choices[0].message.content)