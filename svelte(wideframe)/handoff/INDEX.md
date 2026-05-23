# Storyshelf — handoff index

Open this folder when you start a fresh SvelteKit repo. Files map to:

```
handoff/
├── README.md                         ← start here, file map + how to use
├── CLAUDE.md                         ← drop in repo root; master instructions
├── 01-design-system.md               ← tokens, fonts, motion
├── 02-data-model.md                  ← TS types
├── 03-api-contract.md                ← endpoints + client wrappers
├── 04-routes-and-screens.md          ← sitemap + per-screen acceptance
├── 05-ai-features.md                 ← extraction + chat UX
├── 06-iteration-plan.md              ← order of slices
├── prompts/                          ← paste-and-go for claude-cli
│   ├── 01-setup.md
│   ├── 02-design-system.md
│   ├── 03-api-and-types.md
│   ├── 04-discover.md
│   ├── 05-book-detail.md
│   ├── 06-ai-cast-panel.md
│   ├── 07-character-pages.md
│   ├── 08-profile.md
│   ├── 09-settings.md
│   ├── 10-ai-chat.md
│   └── 11-polish.md
├── skeleton/                         ← drop-in starter files
│   ├── README.md
│   ├── package.json
│   ├── app.css
│   └── vite.config.ts
└── wireframes/                       ← the visual reference (Variant A)
    ├── README.md
    ├── Wireframes.html
    └── *.jsx
```

## Quick start

```bash
# 1. fresh SvelteKit
pnpm dlx sv create storyshelf-web --types ts --no-add-ons --no-install
cd storyshelf-web

# 2. drop handoff inside the repo
mkdir -p docs/handoff
cp -r /path/to/handoff/* docs/handoff/

# 3. move the master file to root
mv docs/handoff/CLAUDE.md ./CLAUDE.md

# 4. start claude-cli inside the repo
claude

# 5. inside claude-cli:
> Read CLAUDE.md and docs/handoff/README.md. Then execute docs/handoff/prompts/01-setup.md.
```

After prompt 01 passes its acceptance checks, move on to prompt 02, and so on
through prompt 11. Each prompt is small enough to fit one claude-cli context
window comfortably with the relevant docs.
