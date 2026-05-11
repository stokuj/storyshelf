# Logout Endpoint JSON Response Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace Spring Security's default 302 redirect on `/api/auth/logout` with a clean `200 {"message":"Logged out successfully"}` JSON response.

**Architecture:** Single change to `SecurityConfig.java` — add a `LogoutSuccessHandler` lambda to the existing `.logout()` configuration block. No changes to `AuthController.java` or frontend code. Integration test uses `@SpringBootTest` + `MockMvc` to verify the full security filter chain.

**Tech Stack:** Spring Boot, Spring Security, MockMvc (spring-security-test), Maven, JUnit 5, AssertJ

---

### Task 1: Add LogoutSuccessHandler to SecurityConfig

**Files:**
- Modify: `backend/backend/src/main/java/com/stokuj/books/security/SecurityConfig.java:48-53`

- [ ] **Step 1: Add `.logoutSuccessHandler(...)` to the logout configuration**

In `SecurityConfig.java`, replace the existing `.logout(...)` block (lines 48-53):

```java
.logout(logout -> logout
        .logoutUrl("/api/auth/logout")
        .invalidateHttpSession(true)
        .deleteCookies("JSESSIONID")
        .permitAll()
)
```

With:

```java
.logout(logout -> logout
        .logoutUrl("/api/auth/logout")
        .logoutSuccessHandler((request, response, authentication) -> {
            response.setStatus(200);
            response.setContentType("application/json");
            response.getWriter().write("{\"message\":\"Logged out successfully\"}");
        })
        .invalidateHttpSession(true)
        .deleteCookies("JSESSIONID")
        .permitAll()
)
```

- [ ] **Step 2: Verify SecurityConfig compiles**

Run: `mvn -B compile -pl backend/backend -q`
Expected: BUILD SUCCESS (no compilation errors)

- [ ] **Step 3: Commit**

```bash
git add backend/backend/src/main/java/com/stokuj/books/security/SecurityConfig.java
git commit -m "feat: add LogoutSuccessHandler returning JSON 200 on logout"
```

---

### Task 2: Write integration test for logout endpoint

**Files:**
- Create: `backend/backend/src/test/java/com/stokuj/books/auth/LogoutIntegrationTest.java`

The logout endpoint is managed by Spring Security's `LogoutFilter` at the security filter chain level — it cannot be tested with the existing Mockito-based `AuthControllerTest`. A `@SpringBootTest` with `MockMvc` is needed to exercise the full filter chain.

- [ ] **Step 1: Write the integration test**

Create `backend/backend/src/test/java/com/stokuj/books/auth/LogoutIntegrationTest.java`:

```java
package com.stokuj.books.auth;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.mock.web.MockHttpServletResponse;
import org.springframework.test.web.servlet.MockMvc;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestBuilders.formLogin;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.csrf;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;

@SpringBootTest
@AutoConfigureMockMvc
class LogoutIntegrationTest {

    @Autowired
    private MockMvc mockMvc;

    @Test
    void shouldReturnJson200OnLogoutWhenAuthenticated() throws Exception {
        mockMvc.perform(formLogin("/api/auth/login")
                        .user("email", "testuser@example.com")
                        .password("password"))
                .andExpect(result -> assertThat(result.getResponse().getRedirectedUrl()).isNull());

        MockHttpServletResponse logoutResponse = mockMvc.perform(
                        post("/api/auth/logout")
                                .contentType(MediaType.APPLICATION_JSON))
                .andReturn()
                .getResponse();

        assertThat(logoutResponse.getStatus()).isEqualTo(200);
        assertThat(logoutResponse.getContentAsString()).isEqualTo("{\"message\":\"Logged out successfully\"}");

        String meBody = mockMvc.perform(get("/api/auth/me"))
                .andReturn()
                .getResponse()
                .getContentAsString();

        assertThat(meBody).contains("\"authenticated\":false");
    }

    @Test
    void shouldReturnJson200OnLogoutWhenUnauthenticated() throws Exception {
        MockHttpServletResponse logoutResponse = mockMvc.perform(
                        post("/api/auth/logout")
                                .with(csrf())
                                .contentType(MediaType.APPLICATION_JSON))
                .andReturn()
                .getResponse();

        assertThat(logoutResponse.getStatus()).isEqualTo(200);
        assertThat(logoutResponse.getContentAsString()).isEqualTo("{\"message\":\"Logged out successfully\"}");
    }
}
```

**Note:** `formLogin` in the authenticated test uses a user registered via `UserDetailsService`. The test relies on a `testuser@example.com` user existing in the database, or a `@TestConfiguration` bean that provides a test user. If `@SpringBootTest` starts with the full application context (including database), a test user must be created first or `UserDetailsService` must be mocked. This test design may need adjustment based on the actual database state and existing test infrastructure.

- [ ] **Step 2: Run the test to see its result**

Run: `mvn -B test -pl backend/backend -Dtest=LogoutIntegrationTest -q`
Expected: depends on database/context setup — may need `@Sql` annotation to pre-populate a test user, or may fail due to missing test user

- [ ] **Step 3: If needed, adjust test for database dependency**

If the test fails because no `testuser@example.com` exists, add an `@Sql` annotation to insert a test user before the test, or use a `@TestConfiguration` with a mock `UserDetailsService`. This is the most likely adjustment needed.

The simplest approach (no `@TestConfiguration` needed if the application boots with a real database):

```java
import org.springframework.test.context.jdbc.Sql;

@Test
@Sql(statements = """
    INSERT INTO users (email, username, password, role, enabled, profile_public)
    VALUES ('testuser@example.com', 'testuser', '$2a$10$dummybcrypthash', 'USER', true, true)
    ON CONFLICT (email) DO NOTHING
""")
void shouldReturnJson200OnLogoutWhenAuthenticated() throws Exception {
    // ... same test body as above
}
```

**Note:** The BCrypt hash value above is placeholder — a real test should use `$2a$10$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36PQ4aG6eVG6eVG6eVG6eVG6e` or generate one with BCrypt.

- [ ] **Step 4: Re-run test to verify it passes**

Run: `mvn -B test -pl backend/backend -Dtest=LogoutIntegrationTest -q`
Expected: BUILD SUCCESS, both tests pass

- [ ] **Step 5: Run full test suite to check for regressions**

Run: `mvn -B test -pl backend/backend -q`
Expected: BUILD SUCCESS, all existing tests still pass

- [ ] **Step 6: Commit**

```bash
git add backend/backend/src/test/java/com/stokuj/books/auth/LogoutIntegrationTest.java
git commit -m "test: add integration test for logout JSON response"
```

---

### Task 3: Update api_endpoints.md

**Files:**
- Modify: `docs/backend/api_endpoints.md:12`

- [ ] **Step 1: Update the logout row**

Replace line 12:

```
| POST | `/api/auth/logout` | Authenticated | Logout and invalidate session |
```

With:

```
| POST | `/api/auth/logout` | Public | Logout, invalidate session. Returns `200 {"message":"Logged out successfully"}` |
```

Also replace line 11 to fix the `GET /api/auth/me` access column for consistency (logout is also public):

```
| GET | `/api/auth/me` | Public/Auth-aware | Return current session identity |
```

With:

```
| GET | `/api/auth/me` | Public | Return current session identity |
```

- [ ] **Step 2: Verify the file looks correct**

Run: `cat docs/backend/api_endpoints.md`
Expected: Lines 11-12 show the updated documentation

- [ ] **Step 3: Commit**

```bash
git add docs/backend/api_endpoints.md
git commit -m "docs: update logout endpoint description with JSON response format"
```
