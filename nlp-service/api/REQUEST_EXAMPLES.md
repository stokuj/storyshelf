# API request examples

`analyse`, `find-pairs`, `ner` maja 2 endpointy:
- `/{book_id}` dla danych z DB
- `/` dla danych bezposrednio z `content`

`relations` ma jeden endpoint: `/relations/`.

## Analyse

### POST /analyse/{book_id}

Przyklad URL:

`/analyse/1`

Body:

```json
{}
```

### POST /analyse/

Body (`content`):

```json
{
  "content": "Bilbo met Gandalf near the Shire."
}
```

## Find Pairs

### POST /find-pairs/{book_id}

Przyklad URL:

`/find-pairs/1`

Body (`names`):

```json
{
  "names": ["Bilbo", "Gandalf", "Thorin"]
}
```

### POST /find-pairs/

Body (`content` + `names`):

```json
{
  "content": "Bilbo met Gandalf. Gandalf spoke with Thorin. Bilbo and Thorin argued.",
  "names": ["Bilbo", "Gandalf", "Thorin"]
}
```

## NER

### POST /ner/{book_id}

Przyklad URL:

`/ner/1`

Body:

```json
{}
```

### POST /ner/

Body (`content`):

```json
{
  "content": "Gandalf visited Bilbo in Hobbiton."
}
```

## Relations

### POST /relations/

Body (`name_1`, `name_2`, `sentences`):

```json
{
  "name_1": "Bilbo",
  "name_2": "Gandalf",
  "sentences": [
    "Gandalf advised Bilbo.",
    "Bilbo trusted Gandalf."
  ]
}
```
