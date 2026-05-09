# API Testing Guide -- Swagger UI

This guide shows how to test all endpoints using **Swagger UI** at `http://localhost:8000/docs`

The API is organized into three groups:
- **Health** -- top-level status endpoints
- **Chapters** -- endpoints under `/chapters/{chapterId}/...`
- **Books** -- endpoints under `/books/{bookId}/...`

---

## 1. Health Endpoints

### 1a. Testing GET /

**Purpose:** Basic welcome message

#### Steps in Swagger UI:
1. Click on **GET /**
2. Click **Try it out**
3. Click **Execute**

#### Expected Response (200 OK):
```json
{
  "message": "Hello World"
}
```

---

### 1b. Testing GET /health/

**Purpose:** Check API and service health

#### Steps in Swagger UI:
1. Click on **GET /health/**
2. Click **Try it out**
3. Click **Execute**

#### Expected Response (200 OK):
```json
{
  "status": "ok",
  "version": "0.6.0",
  "timestamp": "2026-03-09T14:30:45.123456+00:00"
}
```

---

### 1c. Testing GET /health/celery/

**Purpose:** Check Celery worker status

#### Steps in Swagger UI:
1. Click on **GET /health/celery/**
2. Click **Try it out**
3. Click **Execute**

#### Expected Response (200 OK):
```json
{
  "status": "ok",
  "total_workers": 1,
  "total_processes": 4,
  "workers": {
    "celery@worker": {
      "status": "online",
      "active_tasks": 0,
      "concurrency": 4
    }
  }
}
```

#### Possible Response -- Connection Error (503):
```json
{
  "status": "error",
  "error": "Cannot connect to redis"
}
```

---

## 2. Chapters Endpoints

**Important:** All chapters endpoints require `{chapterId}` in the URL and `chapterId` in the request body. These values **must match** -- otherwise the API returns `422 chapterId does not match path`.

Use a concrete ID like `1` for testing.

---

### 2a. Testing POST /chapters/{chapterId}/analyse

**Purpose:** Calculate text statistics (character count, word count, token count)

#### Steps in Swagger UI:
1. Click on **POST /chapters/{chapterId}/analyse**
2. Click **Try it out**
3. Set `chapterId` = `1`
4. Replace the request body with:
```json
{
  "chapterId": "1",
  "content": "Bilbo met Gandalf near the Shire. They discussed the unexpected adventure ahead."
}
```
5. Click **Execute**

#### Expected Response (202 Accepted):
```json
{
  "status": "accepted"
}
```

---

### 2b. Testing POST /chapters/{chapterId}/ner

**Purpose:** Queue an async Named Entity Recognition task via Celery. Returns immediately with `202 Accepted`.

**Rate limit:** 30 requests per minute

#### Steps in Swagger UI:
1. Click on **POST /chapters/{chapterId}/ner**
2. Click **Try it out**
3. Set `chapterId` = `1`
4. Replace the request body with:
```json
{
  "chapterId": "1",
  "content": "In a hole in the ground there lived a hobbit. Bilbo Baggins lived in the Shire with Gandalf the Grey."
}
```
5. Click **Execute**

#### Expected Response (202 Accepted):
```json
{
  "status": "accepted"
}
```

**Note:** NER processing runs asynchronously via Celery. The result is stored by the service, not returned in the HTTP response.

---

## 3. Books Endpoints

**Important:** All books endpoints require `{bookId}` in the URL and `bookId` in the request body. These values **must match** -- otherwise the API returns `422 bookId does not match path`.

Use a concrete ID like `1` for testing.

---

### 3a. Testing POST /books/{bookId}/find-pairs

**Purpose:** Scan text for sentences where specific character pairs appear together

#### Steps in Swagger UI:
1. Click on **POST /books/{bookId}/find-pairs**
2. Click **Try it out**
3. Set `bookId` = `1`
4. Replace the request body with:
```json
{
  "bookId": "1",
  "content": "Bilbo met Gandalf near the Shire. Gandalf spoke with Thorin. Bilbo and Thorin argued about the treasure. Only Gandalf remained calm.",
  "characters": {
    "Bilbo": 1,
    "Gandalf": 1,
    "Thorin": 1
  }
}
```
5. Click **Execute**

#### Expected Response (202 Accepted):
```json
{
  "status": "accepted"
}
```

**Note:** Characters are provided as a dictionary `{"Name": count, ...}`. The service extracts the keys as the character names to search for.

---

### 3b. Testing POST /books/{bookId}/relations

**Purpose:** Extract relations between two characters using an LLM

**Rate limit:** 30 requests per minute

#### Steps in Swagger UI:
1. Click on **POST /books/{bookId}/relations**
2. Click **Try it out**
3. Set `bookId` = `1`
4. Replace the request body with:
```json
{
  "bookId": "1",
  "pairs": [
    {
      "pair": ["Gandalf", "Bilbo"],
      "sentences": [
        "By some curious chance one morning long ago in the quiet of the world, when there was less noise and more green, and the hobbits were still numerous and prosperous, and Bilbo Baggins was standing at his door after breakfast smoking an enormous long wooden pipe that reached nearly down to his wooly toes (neatly brushed) -- Gandalf came by.",
        "Gandalf sat at the head of the party with the thirteen dwarves all around: and Bilbo sat on a stool at the fire-side, nibbling at a biscuit (his appetite was quite taken away), and trying to look as if this was all perfectly ordinary and not in the least an adventure."
      ]
    }
  ]
}
```
5. Click **Execute**

#### Expected Response (202 Accepted):
```json
{
  "status": "accepted"
}
```

**Note:** Each pair requires exactly **2 names** in the `pair` array and at least **1 sentence** in `sentences`.

---

## 4. Common Errors

| HTTP Code | Scenario | Error Detail |
|---|---|---|
| 422 | `chapterId` in URL does not match `chapterId` in body | `chapterId does not match path` |
| 422 | `bookId` in URL does not match `bookId` in body | `bookId does not match path` |
| 422 | Content is empty or whitespace-only | `Content cannot be empty` |
| 422 | Required field missing (e.g., `chapterId`, `content`) | `chapterId is required` |
| 429 | Rate limit exceeded (NER, relations) | `Rate limit exceeded` |
| 503 | Celery/Redis unreachable | `{"status": "error", "error": "..."}` |

---

## 5. Testing Workflow

### Recommended testing order:
1. **Start with `/health/`** to verify API is running
2. **Check `/health/celery/`** to ensure Celery worker is online
3. **Try `/chapters/{chapterId}/analyse`** for a quick synchronous test
4. **Try `/chapters/{chapterId}/ner`** to test async Celery task
5. **Try `/books/{bookId}/find-pairs`** to test text parsing with characters
6. **Try `/books/{bookId}/relations`** to test LLM integration

### Tips:
- **Swagger UI URL:** `http://localhost:8000/docs`
- **Alternative (ReDoc):** `http://localhost:8000/redoc`
- **JSON schema validation:** Swagger UI will show errors if the request format is invalid
- **Copy/Paste:** You can copy responses and use them as templates for other requests
- **Rate limits:** NER and relations are limited to 30 requests per minute per client

---

## 6. Notes

- **NER** (`/chapters/{chapterId}/ner`) is **asynchronous via Celery**. It returns `202 Accepted` immediately and processes in the background.
- **Relations** (`/books/{bookId}/relations`) is **async via LLM**. Each pair requires exactly 2 names and at least 1 sentence.
- **Find Pairs** (`/books/{bookId}/find-pairs`) processes text synchronously but in a thread pool executor.
- All endpoints require `Content-Type: application/json` (Swagger handles this automatically).
- For the Celery worker to process tasks, ensure the `celery-worker` container is running.
