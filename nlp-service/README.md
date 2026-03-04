# storyweave
An educational project for AI-powered character relationship analysis in books and narratives. Extract entities, map connections, and explore the social graph of any story.

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
