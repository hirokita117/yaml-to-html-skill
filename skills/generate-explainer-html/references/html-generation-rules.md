# HTML generation rules

These rules apply when an AI generates the HTML for this skill. In normal use you author
only the **inner iframe view documents**; the outer shell (`index.html`) is written by the
deterministic `scripts/build_html.py`, never by hand. The goal is an **offline,
self-contained, safe** bundle that adapts its explanation UI to the reader, rather than a
fixed template.

The renderer is not the center of this skill. The center is: (1) `core.yaml` meaning,
(2) `view.yaml` strategy, (3) flexible iframe view documents, (4) copyable prompt
templates. These rules keep (3) safe and useful.

The output is a **bundle** (a directory): `index.html` + `views.json` + `core.yaml` /
`view.yaml` + `views/NN-<id>.html` (one per view). The shell's right pane loads one view
at a time via `iframe src="views/<file>"` and a tab switcher; views are **additive** (each
new one becomes another tab).

## Safety rules (hard requirements)

The following are **forbidden** anywhere in the generated HTML (outer or iframe):

- external `<script src=...>`
- external CSS (`<link rel="stylesheet">` or remote `@import`)
- external / remote `<iframe src=...>`
- `<object>`, `<embed>`
- `fetch(...)`
- `XMLHttpRequest`
- `WebSocket`
- `localStorage`
- `sessionStorage`
- `document.cookie`
- access to `window.parent`
- access to `window.top`
- top navigation (`target="_top"`, `window.top.location`, etc.)
- form submit to any endpoint
- embedding API keys or secrets
- embedding large verbatim dumps of the original source text

`scripts/validate_html.py` checks for these patterns and **fails** the build if any are
present. Run it before handing the file to the user. (It also flags any `http://` /
`https://` string, because a truly self-contained file needs none.)

## Allowed

- inline `<style>` (CSS)
- inline `<script>` (JS)
- UI interactions that complete **inside** the iframe
- `<details>` / `<summary>`
- tabs, accordions, filters
- copy buttons (clipboard API with a textarea fallback)
- collapsible trees
- client-side-only interactions (no network, no storage, no frame escape)

## The iframe contract

- The iframe is **required** — it isolates the explanation UI from the shell.
- The shell loads each view through a **local relative `src`** into `views/`. This is a
  local file read, not a network read; remote `src` (scheme `://` or `//`) stays forbidden.
- It **must** carry `sandbox="allow-scripts"`.
- It **must not** include `allow-same-origin` (that would let it reach the parent).

```html
<iframe sandbox="allow-scripts" src="views/01-engineer.html#theme=light"></iframe>
```

Because there is no `allow-same-origin`, the iframe runs in a unique origin and cannot
touch the parent DOM, parent storage, or parent cookies — which is exactly what we want.

> **Browser note:** Chrome/Edge block `file://` iframe subresource loads. Open the bundle
> in Firefox over `file://`, or serve the bundle folder with a trivial local static server
> (which still reads only local files — the no-network rule constrains the *content*).

## Theme contract for each view document

- Each view document is **light by default**.
- The shell cannot style the cross-origin sandboxed iframe directly, so it passes the
  current theme through the iframe URL hash: `views/<file>#theme=dark` or `#theme=light`.
- Each view document must read its **own** `window.location.hash` on load **and** listen to
  `hashchange`, then apply `data-theme="dark"` (or remove it) on `document.documentElement`.
- Provide both a light `:root` palette and a `:root[data-theme="dark"]` palette using CSS
  variables. See `sample-iframe.html` for the exact pattern.

## UI rules

- Choose the representation from the reader's `view.yaml`; do not force one fixed
  template. Prefer understandability over uniformity.
- When there is a lot of information, use **progressive disclosure** (details, tabs,
  "show more") instead of a wall of text.
- Make **importance**, **difficulty**, and **confidence** visually legible (badges,
  color, ordering). Low confidence should look uncertain.
- Always show **source references** so claims are traceable.
- Always show **what to read next** (a reading order / path).
- Always show **good questions to ask an AI next**.
- Mind **accessibility**: semantic headings, labelled controls, visible focus styles,
  sufficient contrast, keyboard-operable interactions.
- Be **responsive**: usable on narrow screens (the shell stacks to one column).
- Respect **`prefers-reduced-motion`**: disable non-essential animation/transition.

## Content rules for the inner UI

The iframe document must not be a flat paragraph dump. It must:

- show the **important concepts** with their importance/difficulty/confidence,
- show the **relations** between concepts,
- show **what to read next**,
- show **source references**,
- show **next questions to ask an AI**,
- match the reader's understanding style from `view.yaml`,
- have **visual structure** (grouping, hierarchy, badges), not just prose.

## Practical generation checklist

1. Read `core.yaml` and `view.yaml` (by the absolute path you were given).
2. Pick forms from `view.yaml.presentation.preferred_forms`; avoid `avoid_forms`.
3. Draft one iframe **view** document (full `<!DOCTYPE html>` document, inline CSS/JS only,
   light default + `#theme` hash handling).
4. Include the required content blocks (concepts, relations, reading order, sources,
   next questions).
5. Author/keep the prompt templates for the shell (see `prompt-template-patterns.md`).
6. Build/grow the bundle with `scripts/build_html.py --bundle <dir> --view-html
   "ラベル=その.html"` (this adds the view as a switchable tab).
7. Validate with `scripts/validate_html.py <dir>/index.html <dir>/views/*.html`; fix any
   finding; re-validate.
8. Hand the user the bundle folder, opened in a browser with no network access (Firefox
   over `file://`, or served locally for Chrome).
