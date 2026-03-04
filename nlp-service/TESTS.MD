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