---
name: canvas-to-github-io
description: >-
  Exports Cursor Canvas (.canvas.tsx) into static HTML for qihao-huang.github.io,
  updates canvases/catalog.json, and wires the homepage Canvas tab. Use when the
  user asks to publish/reuse a canvas on github.io, convert canvas to HTML, or
  add a Canvas catalog entry.
---

# Canvas → github.io

将 Cursor Canvas 导出为可公开访问的静态页，挂到个人站 `qihao-huang.github.io` 的 **Canvas** 导航目录。

## Defaults

| Item | Path |
|------|------|
| Site root | `/home/sany/Documents/Foundation/qihao-huang.github.io` |
| Export dir | `<site>/canvases/` |
| Shared CSS | `<site>/canvases/canvas-shared.css` |
| Shared theme JS | `<site>/canvases/canvas-theme.js` |
| Catalog | `<site>/canvases/catalog.json` |
| Homepage tab | `index.html` → nav `Canvas` → `#canvas` panel |
| Source canvases | `~/.cursor/projects/<workspace>/canvases/*.canvas.tsx` |

Do **not** commit `.canvas.tsx` into github.io unless the user asks. Export **HTML only**.

## Workflow

Copy this checklist and track it:

```
Canvas → github.io:
- [ ] 1. Read source .canvas.tsx
- [ ] 2. Write canvases/<slug>.html (use canvas-shared.css)
- [ ] 3. Upsert canvases/catalog.json entry
- [ ] 4. Ensure index.html has Canvas nav + #canvas panel (once)
- [ ] 5. Local preview (optional)
- [ ] 6. Commit/push only if user asks
```

### 1. Read the canvas

Open the `.canvas.tsx`. Extract:

- Title / subtitle
- Tab labels and section content (tables, callouts, cards, stats, flows)
- Any interactive state that must become plain HTML/JS (tabs → hash buttons)

Ignore `cursor/canvas` imports, `useHostTheme`, `useCanvasState` — reimplement with static HTML + small vanilla JS.

### 2. Write `canvases/<slug>.html`

- `slug` = canvas filename without `.canvas.tsx` (kebab-case).
- In `<head>`: `<meta name="color-scheme" content="light dark">`, then
  `<script src="canvas-theme.js" data-boot></script>`, then
  `<link rel="stylesheet" href="canvas-shared.css">`.
- Topbar must include theme switch (自动 / 浅色 / 深色) sharing `localStorage` key
  `canvas-theme-mode` via `CanvasTheme.init()` at end of body.
- Include top crumb back to catalog: `../index.html#canvas`
- Preserve structure: tabs, tables, cards, callouts, stats.
- Styling comes from `canvas-shared.css` (light + dark via `data-theme` / `prefers-color-scheme`).
- Tab switching: buttons + `.panel.is-active`, sync `location.hash`.
- Escape HTML entities in content (`<`, `>`, `&`).

Topbar pattern:

```html
<div class="topbar">
  <div class="crumb"><a href="../index.html#canvas">← Canvas 目录</a> · <a href="../index.html">首页</a></div>
  <div class="topbar-actions">
    <div class="theme-switch" role="group" aria-label="主题切换">
      <button type="button" class="theme-btn" data-theme-mode="system">自动</button>
      <button type="button" class="theme-btn" data-theme-mode="light">浅色</button>
      <button type="button" class="theme-btn" data-theme-mode="dark">深色</button>
    </div>
    <div class="tiny">Exported from Cursor Canvas</div>
  </div>
</div>
```

Reference implementation: `canvases/lerobot-architecture-map.html`.

### 3. Upsert `canvases/catalog.json`

Array of objects. Newest entries may go first.

```json
{
  "id": "<slug>",
  "title": "<human title>",
  "summary": "<one-line summary>",
  "href": "canvases/<slug>.html",
  "date": "YYYY-MM",
  "tags": ["tag1", "tag2"]
}
```

Homepage loads this file via `fetch` when not on `file://`. Keep a static fallback item in `index.html` `#canvas-catalog` for the first/primary entry if useful.

### 4. Homepage Canvas tab (idempotent)

If missing, ensure `index.html` has:

1. Nav link: `<a href="#canvas" data-panel="canvas">Canvas</a>`
2. Section: `<section id="canvas" class="section view-panel" data-panel="canvas">…</section>` with `#canvas-catalog`
3. `hashToPanel.canvas` / `panelToHash.canvas` mappings
4. `loadCanvasCatalog()` that fetches `canvases/catalog.json` and renders `.publication-item` rows

Do not remove About / Research / Blog / Memo.

### 5. Preview

From site root:

```bash
python3 -m http.server 8000
```

Open `http://localhost:8000/#canvas` then the exported page.

### 6. Git

Only `git add` / `commit` / `push` when the user explicitly asks. Relevant paths:

- `canvases/<slug>.html`
- `canvases/catalog.json`
- `canvases/canvas-shared.css` (if changed)
- `index.html` (if Canvas tab wiring changed)

## Conversion rules

| Canvas SDK | Static HTML |
|------------|-------------|
| `H1` / `H2` / `H3` | `h1` / `h2` / `h3` |
| `Text` / muted | `p.muted` / `.tiny` |
| `Callout` | `.callout` (+ `.warn` / `.ok`) |
| `Card` + header/body | `.card` / `.card-h` / `.card-b` |
| `Stat` | `.stat` with `.v` / `.l` |
| `Table` | `<table>` |
| `Grid columns={n}` | `.grid.grid-n` |
| `Pill` | `.pill` / `.pill.ok` / `.pill.info` |
| `Button` tab bar | `.tab-btn` + JS `activate()` |
| `useCanvasState` tab | `location.hash` |

Do **not** try to bundle React or `cursor/canvas` for github.io. Content export only.

## When user says “把这个 canvas 挂到 github.io”

1. Identify the `.canvas.tsx` path (or the latest one in the workspace canvases dir).
2. Run the workflow above.
3. Reply with local preview URL and the public path after push:  
   `https://qihao-huang.github.io/canvases/<slug>.html`
