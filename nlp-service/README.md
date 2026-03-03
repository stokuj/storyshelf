# storyweave
Educational project for AI-powered person relationship analysis for books and narratives. Extract entities, map connections, and explore the social graph of any story.

---

## Data flow plan
```
Book (PDF / Text)
        ↓
Text Extraction
        ↓
Chunking (token-based, overlap enabled)
        ↓
───────────────────────────────────────
│ 1. NER Model                         │
│    → Extract Characters              │
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

## Changelog

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
Best quality so far has `en_core_web_trf` model.

---

## Decisions:
I decided not to use Spacy at this point because the transformers model is doing a good job of finding characters.