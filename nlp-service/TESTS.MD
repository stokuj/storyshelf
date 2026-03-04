# Testing models & prompts

For all sentences in the book, with names: **["Gandalf", "Bilbo"]**

## qwen3.5-plus-02-15
```JSON
{
  "relations": [
    {
      "source": "Gandalf",
      "relation": "friend_of",
      "target": "Bilbo",
      "evidence": "Anyway by mid-winter Gandalf and Bilbo had come all the way back, along both edges of the Forest, to the doors of Beorn's house; and there for a while they both stayed."
    },
    {
      "source": "Gandalf",
      "relation": "commands",
      "target": "Bilbo",
      "evidence": "Off you go!"
    },
    {
      "source": "Gandalf",
      "relation": "mentor_of",
      "target": "Bilbo",
      "evidence": "Here they sat on wooden benches while Gandalf began his tale, and Bilbo swung his dangling legs and looked at the flowers in the garden..."
    }
  ]
}
```
---

## qwen3.5-35b-a3b
```JSON
{
  "relations": [
    {
      "source": "Gandalf",
      "relation": "commands",
      "target": "Bilbo",
      "evidence": "Off you go!"
    },
    {
      "source": "Gandalf",
      "relation": "friend_of",
      "target": "Bilbo",
      "evidence": "Gandalf and Bilbo had come all the way back, along both edges of the Forest, to the doors of Beorn's house; and there for a while they both stayed."
    },
    {
      "source": "Gandalf",
      "relation": "knows_secret_of",
      "target": "Bilbo",
      "evidence": "Gandalf knew all about the back-door, as the goblins called the lower gate, where Bilbo lost his buttons."
    }
  ]
}
```
---

## qwen3.5-flash-02-23
```JSON
{
  "relations": [
    {
      "source": "Gandalf",
      "relation": "commands",
      "target": "Bilbo",
      "evidence": "\"Off you go!\""
    },
    {
      "source": "Gandalf",
      "relation": "knows_secret_of",
      "target": "Bilbo",
      "evidence": "\"Gandalf knew all about the back-door\""
    },
    {
      "source": "Gandalf",
      "relation": "mentor_of",
      "target": "Bilbo",
      "evidence": "\"Gandalf sat at the head of the party with the thirteen dwarves all around: and Bilbo sat on a stool at the fire-side\""
    },
    {
      "source": "Gandalf",
      "relation": "friend_of",
      "target": "Bilbo",
      "evidence": "\"Gandalf and Bilbo had come all the way back, along both edges of the Forest, to the doors of Beorn's house; and there for a while they both stayed.\""
    }
  ]
}
```

---

## Model cost comparison (pair: Gandalf & Bilbo, full book)

| Model | Input tokens | Output tokens | Cost |
|---|---|---|---|
| `qwen/qwen3.5-flash-02-23` | ~1127 | ~6040–8687 | ~$0.0025–0.0036 |
| `anthropic/claude-sonnet-4-6` | ~1226 | ~323–326 | ~$0.0085 |
| `meta-llama/llama-3.1-8b-instruct` | ~1105 | ~296 | ~$0.000037 |

> Qwen3.5-Flash generates 6000–8000 output tokens due to chain-of-thought "thinking" being enabled by default — significantly increasing cost despite being a "flash" model.

---

## [0.3.0] — 2026-03-04 — 3 pairs (Gandalf, Bilbo, Thorin), full book, qwen3.5-flash-02-23

### Gandalf & Bilbo
```json
{
  "relations": [
    {
      "source": "Gandalf",
      "relation": "commands",
      "target": "Bilbo",
      "evidence": "Off you go!"
    },
    {
      "source": "Gandalf",
      "relation": "friend_of",
      "target": "Bilbo",
      "evidence": "Gandalf and Bilbo had come all the way back, along both edges of the Forest, to the doors of Beorn's house; and there for a while they both stayed."
    },
    {
      "source": "Gandalf",
      "relation": "mentor_of",
      "target": "Bilbo",
      "evidence": "Here they sat on wooden benches while Gandalf began his tale, and Bilbo swung his dangling legs and looked at the flowers in the garden"
    }
  ]
}
```

### Gandalf & Thorin
```json
{
  "relations": [
    {
      "source": "Gandalf",
      "relation": "friend_of",
      "target": "Thorin",
      "evidence": "Gandalf spoke true, as usual!"
    },
    {
      "source": "Gandalf",
      "relation": "protects",
      "target": "Thorin",
      "evidence": "\"They are on their way to visit the land of their fathers, away east beyond Mirkwood.\" put in Gandalf"
    }
  ]
}
```

### Bilbo & Thorin
```json
{
  "relations": [
    {
      "source": "Bilbo",
      "relation": "friend_of",
      "target": "Thorin",
      "evidence": "Baggins, who has proved himself a good companion on our long road"
    },
    {
      "source": "Bilbo",
      "relation": "serves",
      "target": "Thorin",
      "evidence": "perform the service for which he was included in our Company"
    },
    {
      "source": "Thorin",
      "relation": "commands",
      "target": "Bilbo",
      "evidence": "before Thorin gave the word"
    },
    {
      "source": "Thorin",
      "relation": "fights_against",
      "target": "Bilbo",
      "evidence": "said Thorin dropping Bilbo on the top of the wall"
    },
    {
      "source": "Bilbo",
      "relation": "saves",
      "target": "Thorin",
      "evidence": "whispered to him to come out and join his friends"
    }
  ]
}
```