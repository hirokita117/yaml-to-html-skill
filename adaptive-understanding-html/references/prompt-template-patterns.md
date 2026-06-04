# Prompt template patterns (iframe-outside content)

The area **outside** the iframe is not a chat UI. It is a set of **copyable prompt
templates** that let the user ask *another* AI to regenerate or transform the explanation
into a representation that suits them. Each template is a card with a title, a usage
description, the prompt body, a copy button, and optional tags.

`scripts/build_html.py` reads these from a `prompts.json` array and renders the cards.
See `sample-prompts.json` for a working set.

## prompts.json shape

```json
[
  {
    "id": "regenerate-full",
    "title": "HTML全体を再生成する",
    "description": "現在のHTML全体を、希望する表現で再生成したいときに使う",
    "tags": ["full", "regenerate"],
    "prompt": "..."
  }
]
```

- `id` — stable identifier (also used to build the DOM id of the prompt body).
- `title` — card heading.
- `description` — when to use this template.
- `prompt` — the body the user copies. May contain placeholders (below).
- `tags` — optional chips.

## Placeholders

`build_html.py` substitutes two tokens in each `prompt` with the actual file contents:

- `{{core_yaml}}` → contents of the `--core` file
- `{{view_yaml}}` → contents of the `--view` file

Any other `{{...}}` token (for example `{{希望する表現}}`) is **left as-is** so the user
can fill it in before sending. This is how the "free-form" template works.

## Safety wording inside prompt bodies

The prompt text is embedded into the final HTML and scanned by `validate_html.py`.
Phrase the "no external dependency" instruction **generically** so you do not write a
forbidden token (e.g. avoid writing `fetch(`, `XMLHttpRequest`, `localStorage`, or a
`http`/`https` URL inside the prompt). Prefer wording like:

> 制約: 単一の自己完結HTMLを出力。外部CDN・外部CSS・外部スクリプト・外部読み込みの
> iframe を使わない。ネットワーク通信・ブラウザストレージ・cookie・親フレームへの
> アクセスを行わない。iframe は sandbox=allow-scripts のみ。

## Required templates

A generated HTML must include **at least** the following templates outside the iframe.

### 1. Regenerate the whole HTML
**Purpose:** hand the entire current HTML to another AI and get a different representation.
Include: a summary of the target, `{{core_yaml}}`, `{{view_yaml}}`, the desired form, and
the output rules (single self-contained HTML, new understanding UI in the iframe, keep the
prompt templates outside, no external dependency).

### 2. Regenerate only the iframe content
**Purpose:** keep the outer structure, swap only the inner explanation UI.
Include: `{{core_yaml}}`, the current `{{view_yaml}}`, the desired form, and output rules
(output only the iframe's HTML document, inline CSS/JS allowed, no network).

### 3. Table representation
**Purpose:** for readers who think in tables.
Include: concept list, importance, difficulty, relations, evidence, what to read next.

### 4. Worktree representation
**Purpose:** for readers who think in repository structure / hierarchy.
Include: tree view, directory/file/concept hierarchy, where to start reading, high-impact
spots, expandable sections.

### 5. Beginner
**Purpose:** for readers with little prior knowledge.
Include: term explanations, why it matters, a 3-step path to understanding, an analogy,
example questions.

### 6. Engineer
**Purpose:** for implementers / reviewers.
Include: dependencies, changed files, reading order, review points, risks, test angles.

### 7. PdM / Biz
**Purpose:** for readers who care about purpose/impact/decisions over technical detail.
Include: what changes, why it matters, user impact, business impact, decision points,
risks and things to confirm.

### 8. Free-form transform
**Purpose:** let the user describe their own desired representation.
Include a `{{希望する表現}}` placeholder the user fills in.

## Card display spec

Each card contains:

- title
- usage description
- prompt body (shown in a collapsible `<details>` so cards stay compact)
- copy button
- optional tags

The copy button is implemented in JS using the clipboard API, with a **textarea-select
fallback** (`document.execCommand("copy")`) when the clipboard API is unavailable. The
button reads the prompt body's `textContent`, so the copied text is the exact original
(HTML entities resolved), including any substituted `core.yaml` / `view.yaml`.
