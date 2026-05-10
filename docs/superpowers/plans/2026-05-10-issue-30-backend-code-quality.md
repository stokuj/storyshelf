# Issue #30 Backend Code Quality — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Apply 6 backend code quality fixes: optimistic locking, Kafka tx cleanup, error handling, dead code removal, dependency cleanup, logging config.

**Architecture:** Six independent, file-scoped changes to existing Spring Boot backend. No new files created. All changes are annotation/config/delete operations.

**Tech Stack:** Java 21, Spring Boot 4.0.3, Hibernate/JPA, Apache Kafka, Lombok, Maven

---

### Task 1: Add `@Version` optimistic locking to User entity

**Files:**
- Modify: `backend/backend/src/main/java/com/stokuj/books/user/User.java`

- [ ] **Step 1: Add `@Version` field to User.java**

Add the `version` field after the existing `id` field (line 17):

```java
    @Version
    private Long version;
```

Insert after line 17 (`private Long id;`), before the blank line and `email` field. The resulting file should have:

```java
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Version
    private Long version;

    @Column(unique = true, nullable = false)
    private String email;
```

The `@Version` import is already covered by `import jakarta.persistence.*;`.

- [ ] **Step 2: Verify compilation**

```bash
mvn compile -q
```
Expected: BUILD SUCCESS (warnings allowed).

- [ ] **Step 3: Commit**

```bash
git add backend/backend/src/main/java/com/stokuj/books/user/User.java
git commit -m "feat: add @Version optimistic locking to User entity"
```

---

### Task 2: Fix AnalysisResultConsumer — remove @Transactional and add log+skip error handling

**Files:**
- Modify: `backend/backend/src/main/java/com/stokuj/books/integration/kafka/AnalysisResultConsumer.java`

- [ ] **Step 1: Remove @Transactional annotations and import**

Remove the `@Transactional` annotation from all 4 `@KafkaListener` methods (lines 45, 87, 114, 136).

Remove the unused import on line 15:
```java
import org.springframework.transaction.annotation.Transactional;
```

- [ ] **Step 2: Replace 4 IllegalStateException throws with log.warn + return**

**Line 56** — in `consumeAnalyseResult`:
```java
// Before:
throw new IllegalStateException("Chapter not found for analyse result: " + chapterId);
// After:
log.warn("Chapter not found for analyse result: {}", chapterId);
return;
```

**Line 98** — in `consumeNerResult`:
```java
// Before:
throw new IllegalStateException("Chapter not found for ner result: " + chapterId);
// After:
log.warn("Chapter not found for ner result: {}", chapterId);
return;
```

**Line 125** — in `consumeFindPairsResult`:
```java
// Before:
throw new IllegalStateException("Book not found for find-pairs result: " + bookId);
// After:
log.warn("Book not found for find-pairs result: {}", bookId);
return;
```

**Line 147** — in `consumeRelationsResult`:
```java
// Before:
throw new IllegalStateException("Book not found for relations result: " + bookId);
// After:
log.warn("Book not found for relations result: {}", bookId);
return;
```

- [ ] **Step 3: Verify compilation**

```bash
mvn compile -q
```
Expected: BUILD SUCCESS.

- [ ] **Step 4: Commit**

```bash
git add backend/backend/src/main/java/com/stokuj/books/integration/kafka/AnalysisResultConsumer.java
git commit -m "fix: remove @Transactional from Kafka listeners, replace throws with log+skip"
```

---

### Task 3: Delete unused DTOs

**Files:**
- Delete: `backend/backend/src/main/java/com/stokuj/books/integration/dto/AnalyseResponse.java`
- Delete: `backend/backend/src/main/java/com/stokuj/books/integration/dto/AnalyseStats.java`

- [ ] **Step 1: Delete the files**

```bash
rm backend/backend/src/main/java/com/stokuj/books/integration/dto/AnalyseResponse.java
rm backend/backend/src/main/java/com/stokuj/books/integration/dto/AnalyseStats.java
```

- [ ] **Step 2: Verify compilation**

```bash
mvn compile -q
```
Expected: BUILD SUCCESS (no import errors).

- [ ] **Step 3: Commit**

```bash
git add backend/backend/src/main/java/com/stokuj/books/integration/dto/AnalyseResponse.java backend/backend/src/main/java/com/stokuj/books/integration/dto/AnalyseStats.java
git commit -m "chore: remove unused AnalyseResponse and AnalyseStats DTOs"
```

---

### Task 4: Remove unused spring-boot-starter-webflux dependency

**Files:**
- Modify: `backend/backend/pom.xml`

- [ ] **Step 1: Remove the webflux dependency block**

Remove lines 100-103 from pom.xml:
```xml
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-webflux</artifactId>
        </dependency>
```

- [ ] **Step 2: Verify compilation**

```bash
mvn compile -q
```
Expected: BUILD SUCCESS.

- [ ] **Step 3: Commit**

```bash
git add backend/backend/pom.xml
git commit -m "chore: remove unused spring-boot-starter-webflux dependency"
```

---

### Task 5: Add logging configuration

**Files:**
- Modify: `backend/backend/src/main/resources/application.yml`

- [ ] **Step 1: Add logging section to application.yml**

Append at the end of the file (after the `springdoc:` block on line 44):

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

- [ ] **Step 2: Verify compilation**

```bash
mvn compile -q
```
Expected: BUILD SUCCESS (application.yml is loaded at runtime, compile verifies it doesn't break bean creation).

- [ ] **Step 3: Commit**

```bash
git add backend/backend/src/main/resources/application.yml
git commit -m "feat: add logging configuration with per-package levels and file output"
```

---

### Task 6: Final verification

- [ ] **Step 1: Full compilation check**

```bash
mvn compile
```
Expected: BUILD SUCCESS.

- [ ] **Step 2: Run tests**

```bash
mvn test
```
Expected: No new test failures. Pre-existing failures in `RelationsResultProcessorTest` (Lombok setter resolution) are unrelated — confirm the same tests fail on main.

- [ ] **Step 3: Review diff**

```bash
git diff main..HEAD --stat
```
Expected: 6 files changed (User.java, AnalysisResultConsumer.java, AnalyseResponse.java deleted, AnalyseStats.java deleted, pom.xml, application.yml).
