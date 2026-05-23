# 02 · Data model

These are the TypeScript types the frontend will consume. They mirror what your
backend should return — adjust field names where your real API differs, but keep
the shape.

Put each type in its own file under `src/lib/types/` and re-export from
`src/lib/types.ts`.

```ts
// src/lib/types/book.ts
export type BookId = string;

export interface Book {
  id: BookId;
  slug: string;                  // for /books/[slug]
  title: string;
  authors: Author[];
  cover_url: string | null;
  publication_year: number | null;
  genres: string[];
  language: string;              // ISO 639-1
  page_count: number | null;
  description: string | null;
  rating: {
    average: number;             // 0..5
    count: number;
  };
  // Aggregates from backend
  characters_count: number;
  relations_count: number;
  ai_extraction_status: AIExtractionStatus;
}

export interface Author {
  id: string;
  name: string;
  slug: string;
}

export type AIExtractionStatus =
  | 'none'        // never run
  | 'pending'     // queued / running
  | 'ready'       // characters & relations available
  | 'failed';
```

```ts
// src/lib/types/character.ts
import type { BookId } from './book';

export type CharacterId = string;

export interface Character {
  id: CharacterId;
  slug: string;
  name: string;
  also_known_as: string[];       // aliases
  role: CharacterRole;
  short_bio: string | null;      // 1–3 sentences, spoiler-safe
  long_bio: string | null;
  tags: string[];                // 'duke', 'Bene Gesserit', 'POV'
  archetype: string | null;      // 'reluctant chosen one'
  first_appearance_chapter: number | null;
  source: 'human' | 'ai' | 'ai-verified';
  confidence: number | null;     // 0..1, only for AI-sourced
  book_ids: BookId[];            // cross-book characters
  cover_book_id: BookId;         // primary book for routing
}

export type CharacterRole =
  | 'protagonist'
  | 'antagonist'
  | 'supporting'
  | 'minor'
  | 'narrator'
  | 'pov';

export interface Relation {
  id: string;
  book_id: BookId;
  from_character_id: CharacterId;
  to_character_id: CharacterId;
  kind: RelationKind;
  label: string;                 // human-readable e.g. "son / father"
  bidirectional: boolean;
  spoiler_chapter: number | null;// don't show before this chapter
  source: 'human' | 'ai' | 'ai-verified';
  confidence: number | null;
}

export type RelationKind = 'family' | 'romance' | 'ally' | 'enemy' | 'rival' | 'mentor' | 'other';
```

```ts
// src/lib/types/user.ts
export type UserId = string;
export type Visibility = 'public' | 'friends' | 'private';

export interface User {
  id: UserId;
  handle: string;                // 'alex-k'
  display_name: string;
  email: string;
  email_verified: boolean;
  avatar_url: string | null;
  bio: string | null;
  joined_at: string;             // ISO
  followers_count: number;
  following_count: number;
}

export interface UserSettings {
  visibility: Visibility;
  show_real_name: 'public' | 'friends' | 'private';
  show_activity: boolean;
  show_followed_characters: boolean;
  ai_learn_from_notes: boolean;
  indexed_by_search_engines: boolean;
  two_factor_enabled: boolean;
  language: string;
  ai_tone: 'scholarly' | 'casual' | 'concise';
  default_spoiler_limit: 'current-chapter' | 'whole-book' | 'no-limit';
  cite_quotes: 'always' | 'on-request' | 'never';
  notification_email: boolean;
  notification_push: boolean;
}

export interface Shelf {
  id: string;
  name: 'want' | 'reading' | 'read' | string;  // built-in or custom
  is_custom: boolean;
  book_ids: BookId[];
}
```

```ts
// src/lib/types/ai.ts
import type { Character, Relation, BookId } from './character';

export interface AIExtraction {
  id: string;
  book_id: BookId;
  status: 'pending' | 'ready' | 'failed';
  created_at: string;
  finished_at: string | null;
  characters: Character[];
  relations: Relation[];
  // Range covered — for spoiler-safe runs
  covered_through: { chapter: number | null; percentage: number };
  confidence_summary: { overall: number; flagged_low: number };
  failure_reason: string | null;
}

export interface Review {
  id: string;
  book_id: BookId;
  user_id: string;
  rating: number;                // 1..5
  body: string;
  created_at: string;
  likes_count: number;
  ai_summary: string | null;     // optional model summary
}
```

```ts
// src/lib/types.ts — re-exports
export * from './types/book';
export * from './types/character';
export * from './types/user';
export * from './types/ai';
```

## Zod schemas

Mirror the above with **zod** schemas in `src/lib/schemas/`. Use `z.infer` to keep
types and schemas in sync — that way settings forms etc. share the source of truth.
