# P1 Frontend Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add "not found" fallback states to BookDetailView and ProfileView, and a `/health` endpoint for Docker container probes.

**Architecture:** A shared `NotFoundState.vue` component is used in both views via `v-else` blocks. Health endpoint is served by Vite middleware (dev) and nginx location block (prod), with Docker healthchecks in both compose files.

**Tech Stack:** Vue 3 SFC, Vite, nginx, Docker Compose

**Testing:** No frontend test framework exists. Verification: `npm run build` for component syntax/import correctness; `curl` for health endpoint; manual compose healthcheck verification.

---

### Task 1: Create shared NotFoundState component

**Files:**
- Create: `frontend/src/components/NotFoundState.vue`

- [ ] **Step 1: Create the component**

```vue
<template>
  <div class="py-20 text-center flex flex-col items-center gap-4">
    <svg
      xmlns="http://www.w3.org/2000/svg"
      class="w-20 h-20 text-base-content/20"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      stroke-width="1"
    >
      <path
        stroke-linecap="round"
        stroke-linejoin="round"
        d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z"
      />
    </svg>
    <h2 class="text-2xl font-bold">{{ title }}</h2>
    <p v-if="message" class="text-base-content/60">{{ message }}</p>
    <RouterLink v-if="homeLink" to="/" class="btn btn-primary btn-sm mt-2">
      Wróć do strony głównej
    </RouterLink>
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  message: { type: String, default: '' },
  homeLink: { type: Boolean, default: true },
})
</script>
```

- [ ] **Step 2: Verify build passes**

```bash
npm run build
```

Expected: Build succeeds (component compiles, import resolves).

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/NotFoundState.vue
git commit -m "feat: add NotFoundState shared component"
```

---

### Task 2: Add v-else fallback to BookDetailView

**Files:**
- Modify: `frontend/src/views/BookDetailView.vue`

- [ ] **Step 1: Add v-else block and import**

Add import at top of `<script setup>` (line 218):
```js
import NotFoundState from '../components/NotFoundState.vue'
```

Add `v-else` after the closing `</template>` on line 213:
```vue
    </template>

    <template v-else>
      <NotFoundState
        title="Książka nie istnieje"
        message="Nie znaleziono książki o podanym identyfikatorze."
      />
    </template>
  </section>
```

Note: place it right before the closing `</section>` tag (currently line 214).

- [ ] **Step 2: Verify build passes**

```bash
npm run build
```

Expected: Build succeeds with no errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/BookDetailView.vue
git commit -m "fix: add not-found fallback to BookDetailView"
```

---

### Task 3: Add v-else fallback to ProfileView

**Files:**
- Modify: `frontend/src/views/ProfileView.vue`

- [ ] **Step 1: Add v-else block and import**

Add import at top of `<script setup>` (line 63):
```js
import NotFoundState from '../components/NotFoundState.vue'
```

Add `v-else` after the closing `</div>` on line 58 (the card div), before `</section>`:
```vue
    </div>

    <template v-else>
      <NotFoundState
        title="Użytkownik nie znaleziony"
        message="Profil o podanej nazwie nie istnieje."
      />
    </template>
  </section>
```

- [ ] **Step 2: Verify build passes**

```bash
npm run build
```

Expected: Build succeeds with no errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/ProfileView.vue
git commit -m "fix: add not-found fallback to ProfileView"
```

---

### Task 4: Add health middleware to Vite dev server

**Files:**
- Modify: `frontend/vite.config.js`

- [ ] **Step 1: Add configureServer middleware**

```js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

const apiProxyTarget = process.env.VITE_API_PROXY_TARGET || 'http://localhost:8080'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: apiProxyTarget,
        changeOrigin: true,
      },
    },
    configureServer(server) {
      server.middlewares.use('/health', (_req, res) => {
        res.statusCode = 200
        res.setHeader('Content-Type', 'text/plain')
        res.end('OK')
      })
    },
  },
})
```

- [ ] **Step 2: Verify health endpoint responds**

```bash
npm run dev &
sleep 3
curl -s http://localhost:5173/health
```

Expected: Returns `OK` with HTTP 200.

- [ ] **Step 3: Stop dev server and commit**

```bash
kill %1 2>/dev/null
git add frontend/vite.config.js
git commit -m "feat: add /health middleware to Vite dev server"
```

---

### Task 5: Add health location to nginx config

**Files:**
- Modify: `frontend/nginx.conf`

- [ ] **Step 1: Add health location block**

```nginx
server {
    listen 80;
    server_name _;

    root /usr/share/nginx/html;
    index index.html;

    location /health {
        return 200 "OK";
        add_header Content-Type text/plain;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

- [ ] **Step 2: Verify health endpoint in nginx container**

```bash
docker build -f frontend/Dockerfile.prod -t storyshelf-frontend:local frontend/
docker run -d --rm -p 8089:80 --name test-nginx storyshelf-frontend:local
sleep 2
curl -s http://localhost:8089/health
docker stop test-nginx
```

Expected: Returns `OK` with HTTP 200.

- [ ] **Step 3: Commit**

```bash
git add frontend/nginx.conf
git commit -m "feat: add /health location to nginx config"
```

---

### Task 6: Add frontend healthcheck to docker-compose.dev.yml

**Files:**
- Modify: `infra/compose/docker-compose.dev.yml`

- [ ] **Step 1: Add healthcheck to frontend service**

Add to the frontend service block (after `depends_on`):
```yaml
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http://localhost:5173/health"]
      interval: 10s
      timeout: 3s
      retries: 5
```

- [ ] **Step 2: Commit**

```bash
git add infra/compose/docker-compose.dev.yml
git commit -m "feat: add frontend healthcheck to dev compose"
```

---

### Task 7: Add frontend healthcheck to docker-compose.prod.yml

**Files:**
- Modify: `infra/compose/docker-compose.prod.yml`

- [ ] **Step 1: Add healthcheck to frontend service**

Add to the frontend service block (after `depends_on`):
```yaml
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http://localhost:80/health"]
      interval: 10s
      timeout: 3s
      retries: 5
```

- [ ] **Step 2: Commit**

```bash
git add infra/compose/docker-compose.prod.yml
git commit -m "feat: add frontend healthcheck to prod compose"
```

---

### Final Verification

- [ ] Build full frontend: `npm run build` (from `frontend/` dir) — must succeed
- [ ] Review git log: `git log --oneline -7` — should show 7 commits, one per task
