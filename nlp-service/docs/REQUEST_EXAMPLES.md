# API Testing Guide - Swagger UI

This guide shows how to test all endpoints using **Swagger UI** at `http://localhost:8000/docs`

---

## 1. Testing POST /analyse/

**Purpose:** Get text statistics (character count, word count, token count)

### Steps in Swagger UI:
1. Click on **POST /analyse/**
2. Click **Try it out**
3. Replace the request body with:
```json
{
  "content": "Bilbo met Gandalf near the Shire. They discussed the unexpected adventure ahead."
}
```
4. Click **Execute**

### Expected Response (200 OK):
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

## 2. Testing POST /find-pairs/

**Purpose:** Find all sentences containing pairs of specified character names

### Steps in Swagger UI:
1. Click on **POST /find-pairs/**
2. Click **Try it out**
3. Replace the request body with:
```json
{
  "content": "Bilbo met Gandalf near the Shire. Gandalf spoke with Thorin. Bilbo and Thorin argued about the treasure. Only Gandalf remained calm.",
  "names": ["Bilbo", "Gandalf", "Thorin"]
}
```
4. Click **Execute**

### Expected Response (200 OK):
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

## 3. Testing POST /ner/ (Async NER)

**Purpose:** Queue an async Named Entity Recognition task. Returns immediately with a `task_id`.

### Steps in Swagger UI:
1. Click on **POST /ner/**
2. Click **Try it out**
3. Replace the request body with:
```json
{
  "content": "In a hole in the ground there lived a hobbit. Bilbo Baggins lived in the Shire with Gandalf the Grey. They met with the thirteen dwarves led by Thorin Oakenshield."
}
```
4. Click **Execute**

### Expected Response (202 Accepted):
```json
{
  "task_id": "abc12345-def6-7890-ghij-klmnopqrstuv"
}
```

**Note:** Copy the `task_id` value - you'll use it in the next endpoint.

---

## 4. Testing GET /ner/{task_id}

**Purpose:** Poll the status and result of an async NER extraction task

### Steps in Swagger UI:
1. Click on **GET /ner/{task_id}**
2. Click **Try it out**
3. In the `task_id` field, paste the task_id from the previous step (e.g., `abc12345-def6-7890-ghij-klmnopqrstuv`)
4. Click **Execute**

### Expected Response - Still Processing (200 OK):
```json
{
  "task_id": "abc12345-def6-7890-ghij-klmnopqrstuv",
  "state": "PENDING",
  "ready": false
}
```

**Wait a few seconds** and execute again. Once the task completes:

### Expected Response - Task Completed (200 OK):
```json
{
  "task_id": "abc12345-def6-7890-ghij-klmnopqrstuv",
  "state": "SUCCESS",
  "ready": true,
  "result": {
    "engine": "transformers",
    "model_name": "dbmdz/bert-large-cased-finetuned-conll03-english",
    "characters": {
      "Bilbo": 1,
      "Gandalf": 1,
      "Thorin": 1,
      "Oakenshield": 1,
      "Grey": 1
    },
    "organizations": {},
    "locations": {
      "Shire": 1
    },
    "miscellaneous": {},
    "execution_time_seconds": 2.845
  }
}
```

### Possible Response - Task Failed (200 OK):
```json
{
  "task_id": "abc12345-def6-7890-ghij-klmnopqrstuv",
  "state": "FAILURE",
  "ready": true,
  "error": "NER model failed to process text"
}
```

---

## 5. Testing POST /relations/

**Purpose:** Extract relations between two characters using an LLM

### Steps in Swagger UI:
1. Click on **POST /relations/**
2. Click **Try it out**
3. Replace the request body with:
```json
{
  "name_1": "Gandalf",
  "name_2": "Bilbo",
  "sentences": [
    "By some curious chance one morning long ago in the quiet of the world, when there was less noise and more green, and the hobbits were still numerous and prosperous, and Bilbo Baggins was standing at his door after breakfast smoking an enormous long wooden pipe that reached nearly down to his wooly toes (neatly brushed) - Gandalf came by.",
    "Gandalf sat at the head of the party with the thirteen dwarves all around: and Bilbo sat on a stool at the fire-side, nibbling at a biscuit (his appetite was quite taken away), and trying to look as if this was all perfectly ordinary and not in the least an adventure."
  ]
}
```
4. Click **Execute**

### Expected Response (200 OK):
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

## 6. Testing GET /health/ (Bonus)

**Purpose:** Check API and service health

### Steps in Swagger UI:
1. Click on **GET /health/**
2. Click **Try it out**
3. Click **Execute**

### Expected Response (200 OK):
```json
{
  "status": "ok",
  "version": "0.6.0",
  "timestamp": "2026-03-09T14:30:45.123456+00:00"
}
```

---

## Testing Workflow

### Recommended testing order:
1. **Start with `/health/`** to verify API is running
2. **Try `/analyse/`** for a quick synchronous test
3. **Try `/find-pairs/`** to test text parsing with names
4. **Try `/ner/`** followed by `/ner/{task_id}` to test async flow
5. **Try `/relations/`** to test LLM integration

### Tips:
- **Swagger UI URL:** http://localhost:8000/docs
- **Alternative (ReDoc):** http://localhost:8000/redoc
- **JSON schema validation:** Swagger UI will show errors if request format is invalid
- **Copy/Paste:** You can copy responses and use them as templates for other requests
- **Task polling:** For `/ner/{task_id}`, you may need to call it multiple times until `ready: true`

---

## Notes

- **NER** (`/ner/`) is **asynchronous via Celery**. It returns immediately with a task_id, so you must poll `/ner/{task_id}` for results.
- **Relations** (`/relations/`) requires exactly **2 names** and at least **1 sentence**.
- **Find Pairs** (`/find-pairs/`) requires at least **2 names**.
- All endpoints require `Content-Type: application/json` (Swagger handles this automatically).
- For the Celery worker to process tasks, ensure the `celery-worker` container is running.
