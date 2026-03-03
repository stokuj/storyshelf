from openai import OpenAI
import os

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

prompt = """
Masz listę postaci:
[Harry, Snape]

Fragment:

"Harry spotkał Snape'a w korytarzu. Snape ostrzegł go."

Wyciągnij relacje.
Zwróć tylko JSON.
"""

response = client.chat.completions.create(
    model="meta-llama/llama-3.1-8b-instruct",
    messages=[
        {"role": "system", "content": "Ekstrakcja relacji."},
        {"role": "user", "content": prompt}
    ],
)

print(response.choices[0].message.content)