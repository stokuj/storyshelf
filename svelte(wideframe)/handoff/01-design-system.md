# 01 · Design system

The visual target for Variant A is **literary, warm, restrained**. Think modern
indie bookshop website, not Web3 dashboard. Paper feel, generous typography,
one warm accent, no gradients.

## Color tokens

Define these in `src/app.css` under `@theme` (Tailwind v4 native).

```css
/* src/app.css */
@import "tailwindcss";

@theme {
  /* Brand */
  --color-paper: oklch(0.975 0.012 80);      /* warm off-white background */
  --color-paper-2: oklch(0.955 0.018 80);    /* secondary surface (cards on bg) */
  --color-surface: oklch(0.995 0.005 80);    /* primary card */
  --color-ink: oklch(0.20 0.015 50);         /* primary text */
  --color-ink-2: oklch(0.32 0.018 50);       /* secondary text */
  --color-muted: oklch(0.56 0.015 60);       /* muted text */
  --color-rule: oklch(0.88 0.012 70);        /* borders, dividers */
  --color-rule-strong: oklch(0.78 0.014 70); /* card outlines */

  /* Accent — terracotta, used sparingly */
  --color-accent: oklch(0.62 0.155 45);        /* primary accent */
  --color-accent-hover: oklch(0.56 0.165 45);
  --color-accent-soft: oklch(0.93 0.045 60);   /* AI panel background tint */
  --color-accent-ink: oklch(0.30 0.10 45);     /* accent text on accent-soft */

  /* Semantic */
  --color-success: oklch(0.62 0.13 145);
  --color-danger: oklch(0.58 0.18 18);
  --color-warning: oklch(0.74 0.14 75);
  --color-info: oklch(0.60 0.13 235);

  /* Relation kinds (for the graph + badges) */
  --color-rel-family: oklch(0.55 0.13 250);
  --color-rel-romance: oklch(0.60 0.16 0);
  --color-rel-ally: oklch(0.58 0.12 150);
  --color-rel-enemy: oklch(0.60 0.18 30);

  /* Dark mode overrides — class-based */
}

@layer base {
  .dark {
    --color-paper: oklch(0.16 0.012 60);
    --color-paper-2: oklch(0.20 0.014 60);
    --color-surface: oklch(0.22 0.015 60);
    --color-ink: oklch(0.94 0.008 80);
    --color-ink-2: oklch(0.80 0.012 80);
    --color-muted: oklch(0.62 0.012 70);
    --color-rule: oklch(0.30 0.012 70);
    --color-rule-strong: oklch(0.42 0.014 70);
    --color-accent-soft: oklch(0.28 0.06 55);
  }
}
```

## Typography

Use Google Fonts. Load in `src/app.html`:

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;0,6..72,700;1,6..72,400&family=Public+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
```

Tokens:

```css
@theme {
  --font-display: "Newsreader", "Iowan Old Style", Georgia, serif;
  --font-sans: "Public Sans", ui-sans-serif, system-ui, sans-serif;
  --font-mono: ui-monospace, "SF Mono", Menlo, monospace;
}
```

Scale (use Tailwind defaults — `text-xs` … `text-5xl`). Conventions:

- **Display / page H1** — `font-display text-4xl md:text-5xl tracking-tight font-medium` (Newsreader). Optical sizing on.
- **Section heading** — `font-display text-2xl font-medium`.
- **Card title / book title** — `font-sans text-base font-semibold`.
- **Body** — `font-sans text-[15px] leading-relaxed text-ink`.
- **Metadata / labels** — `font-sans text-xs uppercase tracking-wider text-muted`.
- Book authors and quotes set in **italic Newsreader 400** (`font-display italic`).

## Spacing & layout

- Container max-width: `max-w-[1240px] mx-auto px-6 md:px-10`.
- Grid gutters: `gap-6` (cards), `gap-10` (sections).
- Book cover aspect: `2 / 3`. Sizes: xs=48, sm=72, md=112, lg=180, xl=260 (CSS width in px).
- Avatar sizes: sm=32, md=40, lg=56, xl=80.

## Radii & elevation

```css
@theme {
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 14px;
  --radius-pill: 999px;
}
```

Shadow: **avoid** elevation shadows on cards. Use 1px borders (`border border-rule`)
plus a hover `border-rule-strong`. Reserve drop-shadow for modals and the AI panel:

```
.ai-panel { @apply bg-accent-soft border border-rule rounded-lg; }
.modal    { @apply shadow-2xl; }
```

## Motion

- Standard transition: `transition-colors duration-200 ease-out` or `transition-transform`.
- Pages enter via SvelteKit's default — don't add custom page transitions.
- Loading: `Skeleton` from shadcn-svelte. For AI streaming, a subtle pulsing dot:
  ```svelte
  <span class="inline-block w-2 h-2 rounded-full bg-accent animate-pulse" />
  ```

## Iconography

`lucide-svelte`. Default size `size={16}` inline, `size={20}` for nav, `size={24}` for empty
states. Stroke width 1.75.

Avoid emoji in production UI (only OK in book/character data the model returns).

## "AI" visual language

Anywhere AI output is shown, mark it with **one** of these (never more than one per region):

- A small `<AIBadge>` chip — `bg-accent-soft text-accent-ink ring-1 ring-accent/30`, with a
  Lucide `Sparkles` icon, 12px text.
- A dashed border in `border-accent/40` on the container.
- A `text-accent` `Sparkles` icon prefix on the section heading.

This keeps user-generated content distinguishable from model-generated content at a glance.
