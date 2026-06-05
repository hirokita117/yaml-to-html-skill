# HTML generation rules

These rules apply when an AI generates the HTML for this skill — both the outer shell and
the inner iframe document. The goal is a **single, offline, self-contained, safe** HTML
file that adapts its explanation UI to the reader, rather than a fixed template.

The renderer is not the center of this skill. The center is: (1) `core.yaml` meaning,
(2) `view.yaml` strategy, (3) flexible iframe UI, (4) copyable prompt templates. These
rules keep (3) safe and useful.

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
- Display it with `srcdoc` (preferred) or safe JS injection of a string.
- It **must** carry `sandbox="allow-scripts"`.
- It **must not** include `allow-same-origin` (that would let it reach the parent).

```html
<iframe sandbox="allow-scripts" srcdoc="...escaped document..."></iframe>
```

Because there is no `allow-same-origin`, the iframe runs in a unique origin and cannot
touch the parent DOM, parent storage, or parent cookies — which is exactly what we want.

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

1. Read `core.yaml` and `view.yaml`.
2. Pick forms from `view.yaml.presentation.preferred_forms`; avoid `avoid_forms`.
3. Draft the iframe document (full `<!DOCTYPE html>` document, inline CSS/JS only).
4. Include the required content blocks (concepts, relations, reading order, sources,
   next questions).
5. Draft the prompt templates for the shell (see `prompt-template-patterns.md`).
6. Assemble with `scripts/build_html.py`.
7. Validate with `scripts/validate_html.py`; fix any finding; re-validate.
8. Hand the user a file that opens directly in a browser with no network access.
