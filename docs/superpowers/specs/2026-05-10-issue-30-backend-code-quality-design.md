# Design: Issue #30 — Backend Code Quality

## Summary

6 non-blocking code quality fixes identified during backend audit. All changes are isolated, low-risk improvements to code hygiene.

## Decisions Made

- **Kafka error handling**: Log + skip (replace `IllegalStateException` throws with `log.warn` + `return`)
- **Unused DTOs**: Delete files (not wire up)
- **Logging levels**: `com.stokuj.books` DEBUG, Spring/Kafka/Hibernate WARN, default INFO, file output

---

## Item 1: Optimistic Locking on `User` Entity

**File**: `backend/backend/src/main/java/com/stokuj/books/user/User.java`

**Change**: Add `@Version private Long version;` field.

**Rationale**: Without `@Version`, concurrent updates to the same `User` silently overwrite each other (last write wins). Hibernate's `@Version` enables optimistic locking — if two transactions update the same entity, the second commit fails with `OptimisticLockException`.

**Approach**: Single field addition. Hibernate manages the version column automatically (auto-creates migration via Flyway if `ddl-auto` allows, or manual migration needed).

---

## Item 2: Remove `@Transactional` from `@KafkaListener` Methods

**File**: `backend/backend/src/main/java/com/stokuj/books/integration/kafka/AnalysisResultConsumer.java`

**Change**: Remove `@Transactional` annotation from all 4 `@KafkaListener` methods (lines 45, 87, 114, 136).

**Rationale**: `@Transactional` on Kafka listeners is an anti-pattern. Kafka commits offsets outside the transaction boundary, so a rollback doesn't undo the offset commit, causing message loss. The called processors (`NerResultProcessor`, `RelationsResultProcessor`) already have `@Transactional` on their methods. `consumeAnalyseResult` uses Spring Data JPA repositories which are transactional by default.

**Approach**: Remove the 4 `@Transactional` annotations and the unused import. No new `@Transactional` additions needed.

---

## Item 3: Kafka Listener Error Handling — Log + Skip

**File**: `backend/backend/src/main/java/com/stokuj/books/integration/kafka/AnalysisResultConsumer.java`

**Change**: Replace 4× `throw new IllegalStateException(...)` with `log.warn(...); return;`.

**Locations**:
- Line 56: Chapter not found in `consumeAnalyseResult`
- Line 98: Chapter not found in `consumeNerResult`
- Line 125: Book not found in `consumeFindPairsResult`
- Line 147: Book not found in `consumeRelationsResult`

**Rationale**: Throwing from a `@KafkaListener` without a configured error handler causes Kafka to retry indefinitely. "Not found" is not a transient error — retrying won't fix it. Logging and skipping is the correct approach.

---

## Item 4: Remove Unused DTOs

**Files to delete**:
- `backend/backend/src/main/java/com/stokuj/books/integration/dto/AnalyseResponse.java`
- `backend/backend/src/main/java/com/stokuj/books/integration/dto/AnalyseStats.java`

**Rationale**: Confirmed via codebase search — zero imports of either class anywhere. The Kafka consumer uses `Map<String, Object>` for deserialization instead.

---

## Item 5: Remove Unused `spring-boot-starter-webflux` Dependency

**File**: `backend/backend/pom.xml`

**Change**: Remove lines 100-103 (the `spring-boot-starter-webflux` dependency block).

**Rationale**: The project uses Spring WebMVC, not WebFlux. Zero usage of `WebClient` anywhere in the codebase (confirmed via search). Removing reduces dependency footprint and startup time.

---

## Item 6: Add Logging Configuration

**File**: `backend/backend/src/main/resources/application.yml`

**Change**: Add `logging:` section at the end of the file:

```yaml
logging:
  level:
    root: INFO
    com.stokuj.books: DEBUG
    org.springframework: WARN
    org.apache.kafka: WARN
    org.hibernate: WARN
  file:
    name: logs/springshelf.log
```

**Rationale**: Currently everything logs at default INFO with no file output. Per-package levels give application code DEBUG visibility while keeping framework noise at WARN. File output enables persistent log access.

---

## Files Changed

| File | Change |
|------|--------|
| `User.java` | Add `@Version` field |
| `AnalysisResultConsumer.java` | Remove `@Transactional`, replace throws with log+skip |
| `AnalyseResponse.java` | Delete |
| `AnalyseStats.java` | Delete |
| `pom.xml` | Remove webflux dependency |
| `application.yml` | Add logging config |

## Verification

- `mvn compile` — must pass
- `mvn test` — must pass (pre-existing test failures in `RelationsResultProcessorTest` are unrelated and present on main; verify no new failures)
