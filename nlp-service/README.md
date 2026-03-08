# storyweave
An educational project for AI-powered character relationship analysis in books and narratives. Extract entities, map connections, and explore the social graph of any story.

Currently using FastAPI with docker.

---
## Endpoints

The API currently exposes 9 endpoints.

- `GET /` - Basic hello route.
- `GET /health/` - Service health check with NER model load status.
- `POST /analyse/{book_id}` - Returns book content loaded from DB by `book_id`.
- `POST /analyse/` - Returns content passed directly in the request body.
- `POST /find-pairs/{book_id}` - Finds character pairs and matching sentences using DB book content.
- `POST /find-pairs/` - Finds character pairs and matching sentences using direct `content` input.
- `POST /ner/{book_id}` - Runs NER on book content loaded from DB.
- `POST /ner/` - Runs NER on direct `content` input.
- `POST /relations/` - Extracts relations for exactly two names (`name_1`, `name_2`) from provided `sentences`.


## Data flow plan
```
Book (PDF / Text)
        ↓
Text Extraction
        ↓
(Optional spliting text into parts)
        ↓
───────────────────────────────────────
│ 1. NER Model (bert-large-cased)      │
│    → Extract Characters              │
───────────────────────────────────────
        ↓
───────────────────────────────────────
│ #TODO Coreference Model              │
│    → coreference resolution          │
│    → entity normalization            │
───────────────────────────────────────
        ↓    
Person List (JSON)
        ↓
Generate Person Pairs
        ↓
Extract Sentences Containing Person Pairs
        ↓
───────────────────────────────────────
│ 2. LLM Attribute Extraction          │
│    → Age                             │
│    → Gender                          │
│    → Other facts                     │
───────────────────────────────────────
        ↓
───────────────────────────────────────
│ 3. LLM Relation Extraction           │
│    → Relation triples                │
│    (source, relation, target)        │
───────────────────────────────────────
        ↓
Graph Database (Neo4j)
        ↓
Structured Knowledge Graph
```

---

## Example relation extraction
### Input

```python
names = ["Gandalf", "Bilbo"]
sentences = ['By some curious chance one morning long ago in the quiet of the world, when there was less noise and more green, and the hobbits were still numerous and prosperous, and Bilbo Baggins was standing at his door after breakfast smoking an enormous long wooden pipe that reached nearly down to his wooly toes (neatly brushed) - Gandalf came by.', 'Gandalf sat at the head of the party with the thirteen dwarves all around: and Bilbo sat on a stool at the fire-side, nibbling at a biscuit (his appetite was quite taken away), and trying to look as if this was all perfectly ordinary and not in the least an adventure.']
```
### Llama-3.1-8b
```json
{
  "relations": [
    {
      "source": "Gandalf",
      "relation": "mentor_of",
      "target": "Bilbo",
      "evidence": "Gandalf came by"
    },
    {
      "source": "Gandalf",
      "relation": "commands",
      "target": "dwarves",
      "evidence": "Gandalf sat at the head of the party"
    },
    {
      "source": "Gilraen",
      "relation": "admires",
      "target": "Bilbo",
      "evidence": "his appetite was quite taken away"
    },
    {
      "source": "Bilbo",
      "relation": "friend_of",
      "target": "dwarves",
      "evidence": "he was trying to look as if this was all perfectly ordinary and not in the least an adventure."
    }
  ]
}
```

### Claude Sonnet 4.6
```json
{
  "relations": [
    {
      "source": "Gandalf",
      "relation": "commands",
      "target": "Bilbo",
      "evidence": "Gandalf sat at the head of the party with the thirteen dwarves all around: and Bilbo sat on a stool at the fire-side, nibbling at a biscuit (his appetite was quite taken away), and trying to look as if this was all perfectly ordinary and not in the least an adventure."
    }
  ]
}
```

## Changelog

### [0.5.1] - 2026-03-08

- Removed database layer (`api/db/database.py`) and commented out all DB-dependent routes.
- Switched `LLMService` from synchronous `OpenAI` to `AsyncOpenAI` and refactored it into a module-level singleton.
- Expanded NER extraction from persons-only to four entity types: characters, organizations, locations, and miscellaneous.
- Replaced the deprecated `@app.on_event("startup")` with a `lifespan` context manager and centralized `load_dotenv()` in `app.py`.
- Added 14 tests with `pytest`, `httpx`, and `coverage` as new dependencies.
- Planned future integration of Celery with dynamic workers to offload the NER model from the FastAPI process.

### [0.5.0] — 2026-03-06

API routing and inference startup were refactored:

- Split API into 4 router categories: `analyse`, `find-pairs`, `ner`, `relations`
- Standardized dual input flow for `analyse`, `find-pairs`, and `ner`:
  - `POST /<category>/{book_id}` reads content from DB
  - `POST /<category>/` accepts direct `content` in request body
- Simplified `relations` to one endpoint: `POST /relations/` with `name_1`, `name_2`, and `sentences`
- Simplified pair-search logic in `book_service.py` to one readable function with optional `include_empty` mode
- Added NER model preloading on app startup and exposed model load status in `GET /health/`
- Added request payload examples in `api/REQUEST_EXAMPLES.md`

---

### [0.3.0] — 2026-03-04

Integrated LLM relation extraction into the main pipeline:

- `llm.py` refactored from a standalone script into `LLMService` class with `extract_relations(pair, sentences)` method
- `find_pair_sentences` now searches the entire book instead of a single chapter, and returns `list[dict]` instead of a JSON string
- `main.py` now iterates over all character pairs and calls `LLMService` for each one
- First run with 3 characters (Gandalf, Bilbo, Thorin) — 3 pairs extracted, 10 relations total (see [TESTS.MD](TESTS.MD))

---

### [0.2.0] — 2026-03-03
Benchmarked 4 NER models on Chapter 1 of *The Hobbit*:

- **dslim/bert-base-NER (Transformers)** — 12.24s  
  → Good coverage (Gandalf, Bilbo, Thorin detected). Minor false positives (`At`, `Bull`, `Mr`).

- **dbmdz/bert-large-cased-finetuned-conll03-english (Transformers)** — 33.48s  
  → Worst time/quality ratio. Token splitting issues (`So Thorin`, `Thr`, `roarer`). Discarded.

- **en_core_web_sm (spaCy)** — 1.39s  
  → Fastest but misses key characters (Gandalf, Thorin absent). Many false positives. Discarded as primary.

- **en_core_web_trf (spaCy Transformer)** — 12.11s  
  → Best quality. Full cast detected, fewest false positives. Selected as production model.

**Conclusion:**  
`en_core_web_trf` and `dslim/bert-base-NER` are comparable in quality (~12s). `trf` selected for cleaner output.

---

### [0.1.0] — 2026-03-03

Benchmarked 3 NER models on Chapter 1 of *The Hobbit*:

- **dslim/bert-base-NER (Transformers)** — 0.49s  
  → Only 1 entity detected (token aggregation issue). Result discarded.

- **en_core_web_sm (spaCy)** — 1.58s  
  → Detects main persons but produces many false positives (e.g. common words treated as entities) and misses key persons such as Gandalf.

- **en_core_web_trf (spaCy Transformer)** — 10.59s  
  → Highest extraction quality, correctly identifies full person names.  
  → Selected as the production model despite higher computational cost.

**Conclusion:**  
`en_core_web_trf` has the best quality so far.

---

## Decisions

I decided not to use spaCy at this point because the Transformers model is doing a good job of finding characters.

Writing a good prompt is hard; it will take a lot of time to fine-tune things.
At this point I can already tell that I need more relation types, or I need better accuracy with the existing ones.
I will also need to include sentence positions to track the progression of character relationship development.
