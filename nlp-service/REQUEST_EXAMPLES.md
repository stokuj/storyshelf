# API Request Examples

All endpoints accept direct text input. The API currently exposes 4 main endpoints (plus helper endpoints for task status).

---

## 1. POST /analyse/

Analyze text statistics: character count, word count, and estimated token count.

### Request

```bash
curl -X POST http://localhost:8000/analyse/ \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Bilbo met Gandalf near the Shire. They discussed the unexpected adventure ahead."
  }'
```

### Response (200 OK)

```json
{
  "analysis": {
    "char_count": 88,
    "word_count": 16,
    "token_count": 22
  }
}
```

---

## 2. POST /find-pairs/

Find all sentences containing any pair of specified character names.

### Request

```bash
curl -X POST http://localhost:8000/find-pairs/ \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Bilbo met Gandalf near the Shire. Gandalf spoke with Thorin. Bilbo and Thorin argued about the treasure. Only Gandalf remained calm.",
    "names": ["Bilbo", "Gandalf", "Thorin"]
  }'
```

### Response (200 OK)

```json
{
  "pairs": [
    {
      "name_a": "Bilbo",
      "name_b": "Gandalf",
      "sentences": [
        "Bilbo met Gandalf near the Shire."
      ]
    },
    {
      "name_a": "Gandalf",
      "name_b": "Thorin",
      "sentences": [
        "Gandalf spoke with Thorin."
      ]
    },
    {
      "name_a": "Bilbo",
      "name_b": "Thorin",
      "sentences": [
        "Bilbo and Thorin argued about the treasure."
      ]
    }
  ]
}
```

---

## 3. POST /ner/ (Async Named Entity Recognition)

Queue an async NER task to extract named entities (characters, organizations, locations, misc) from text. Returns a `task_id` immediately.

### Request

```bash
curl -X POST http://localhost:8000/ner/ \
  -H "Content-Type: application/json" \
  -d '{
    "content": "In a hole in the ground there lived a hobbit. Bilbo Baggins lived in the Shire with Gandalf the Grey. They met with the thirteen dwarves led by Thorin Oakenshield."
  }'
```

### Response (202 Accepted)

```json
{
  "task_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479"
}
```

---

## 4. GET /ner/{task_id}

Poll the status and result of an async NER extraction task.

### Request (Pending)

```bash
curl http://localhost:8000/ner/f47ac10b-58cc-4372-a567-0e02b2c3d479
```

### Response (Task still processing)

```json
{
  "task_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "state": "PENDING",
  "ready": false
}
```

### Response (Task completed successfully)

```json
{
  "task_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "state": "SUCCESS",
  "ready": true,
  "result": {
    "engine": "transformers",
    "model_name": "dbmdz/bert-large-cased-finetuned-conll03-english",
    "characters": {
      "Bilbo": 1,
      "Gandalf": 1,
      "Thorin": 1,
      "Oakenshield": 1
    },
    "organizations": {},
    "locations": {
      "Shire": 1
    },
    "miscellaneous": {},
    "execution_time_seconds": 3.245
  }
}
```

### Response (Task failed)

```json
{
  "task_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "state": "FAILURE",
  "ready": true,
  "error": "NER model failed to load: CUDA out of memory"
}
```

---

## 5. POST /relations/

Extract relations between two characters using an LLM. Provide character names and sentences containing both characters.

### Request

```bash
curl -X POST http://localhost:8000/relations/ \
  -H "Content-Type: application/json" \
  -d '{
    "name_1": "Gandalf",
    "name_2": "Bilbo",
    "sentences": [
      "By some curious chance one morning long ago in the quiet of the world, when there was less noise and more green, and the hobbits were still numerous and prosperous, and Bilbo Baggins was standing at his door after breakfast smoking an enormous long wooden pipe that reached nearly down to his wooly toes (neatly brushed) - Gandalf came by.",
      "Gandalf sat at the head of the party with the thirteen dwarves all around: and Bilbo sat on a stool at the fire-side, nibbling at a biscuit (his appetite was quite taken away), and trying to look as if this was all perfectly ordinary and not in the least an adventure."
    ]
  }'
```

### Response (200 OK)

```json
{
  "pair": [
    "Gandalf",
    "Bilbo"
  ],
  "sentences_count": 2,
  "relations": {
    "relations": [
      {
        "source": "Gandalf",
        "relation": "mentor_of",
        "target": "Bilbo",
        "evidence": "Gandalf came by."
      },
      {
        "source": "Gandalf",
        "relation": "commands",
        "target": "Bilbo",
        "evidence": "Gandalf sat at the head of the party"
      }
    ]
  }
}
```

---

## Health Check

### Request

```bash
curl http://localhost:8000/health/
```

### Response (200 OK)

```json
{
  "status": "ok",
  "version": "0.6.0",
  "timestamp": "2026-03-09T10:30:45.123456"
}
```

---

## Notes

- **NER** (`/ner/`) is async via Celery. Always check task status with `GET /ner/{task_id}` after receiving a task ID.
- **Relations** (`/relations/`) requires exactly 2 names and at least 1 sentence.
- **Find Pairs** (`/find-pairs/`) requires at least 2 names.
- All endpoints require `Content-Type: application/json` for POST requests.
