# storyweave
Educational project for AI-powered character relationship analysis for books and narratives. Extract entities, map connections, and explore the social graph of any story.

---

## Changelog

### [0.1.0] — 2026-03-03

Benchmarked 3 NER models on Chapter 1 of *The Hobbit*:

- **dslim/bert-base-NER (Transformers)** — 0.49s  
  → Only 1 entity detected (token aggregation issue). Result discarded.

- **en_core_web_sm (spaCy)** — 1.58s  
  → Detects main characters but produces many false positives (e.g. common words treated as entities) and misses key characters such as Gandalf.

- **en_core_web_trf (spaCy Transformer)** — 10.59s  
  → Highest extraction quality, correctly identifies full character names.  
  → Selected as the production model despite higher computational cost.

**Conclusion:**  
Best quality so far has `en_core_web_trf` model.