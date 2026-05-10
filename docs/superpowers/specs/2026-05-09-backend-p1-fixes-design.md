# Backend P1 Fixes — Design Spec

Issue: [#21](https://github.com/stokuj/storyshelf/issues/21)
Date: 2026-05-09

Four backend bugs in the Kafka integration pipeline.

## Fix 1: Atomic NER Completed Counter

**File:** `NerResultProcessor.java` + `BookRepository.java`

**Problem:** `book.setNerCompletedCount(book.getNerCompletedCount() + 1)` is a non-atomic read-modify-write in Java. Two concurrent NER results for the same book can race, producing an incorrect counter and preventing `find-pairs` from ever being triggered.

**Fix:**
- Add atomic SQL query to `BookRepository`: `@Modifying @Query("UPDATE Book b SET b.nerCompletedCount = b.nerCompletedCount + 1 WHERE b.id = :id")`
- Replace `book.setNerCompletedCount(...); bookRepository.save(book)` with `bookRepository.incrementNerCompletedCount(book.getId())`
- Remove the `bookRepository.save(book)` call entirely (no other Book fields are mutated in this method)

## Fix 2: Per-Relation Dedup

**Files:** `AnalysisResultConsumer.java` + `RelationsResultProcessor.java`

**Problem:** `consumeRelationsResult()` checks `hasResolvedRelations` globally — if ANY single character relation for a book already has a non-blank `relation` string, the ENTIRE relations batch is skipped. Partial batches (where some relations are resolved and others are not) are silently dropped.

**Fix:**
- Remove global pre-check (lines 140-146) in `AnalysisResultConsumer.consumeRelationsResult()`
- Add per-relation skip in `RelationsResultProcessor.processRelationsResult()`: if the existing relation (found via `findByBookIdAndSourceIdAndTargetId`) already has a non-blank `relation`, skip that individual pair

## Fix 3: Missing Stats Field Validation

**File:** `AnalysisResultConsumer.java`

**Problem:** `charCount`, `charCountClean`, `wordCount`, `tokenCount` are silently set to `null` when both snake_case and camelCase keys are missing from the payload. No warning or error is logged.

**Fix:**
- Add `log.warn(...)` for each stat field that resolves to `null`, including the `chapterId` for debugging

## Fix 4: Explicit Kafka Serializer Type

**Files:** `ChapterEventProducer.java`

**Problem:** `sendBookForRelations()` accepts `List<?>` — raw, untyped list. The underlying `PairResult` record may not serialize correctly without explicit type information.

**Fix:**
- Change `List<?>` to `List<PairResult>` in method signature
- Jackson handles Java record serialization automatically (if `jackson-databind` is on classpath)

## Testing Strategy

- Unit tests using Mockito + AssertJ (matching existing project conventions)
- One test class per fix, following project patterns (`@ExtendWith(MockitoExtension.class)`)
- No integration tests with Kafka/DB containers

## Affected Files

| File | Fix 1 | Fix 2 | Fix 3 | Fix 4 |
|------|-------|-------|-------|-------|
| `NerResultProcessor.java` | x | | | |
| `BookRepository.java` | x | | | |
| `AnalysisResultConsumer.java` | | x | x | |
| `RelationsResultProcessor.java` | | x | | |
| `ChapterEventProducer.java` | | | | x |
