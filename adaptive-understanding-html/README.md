# adaptive-understanding-html

A Claude skill that turns an **understanding target** — a document, repository summary,
pull request / diff, README, design note, or specification — into **one self-contained
HTML file** tailored to how a particular reader understands things.

The HTML has two parts:

- **Inside an iframe:** a visual explanation UI for the target (table, worktree, cards,
  FAQ, comparison, sequence, reading path, risk/impact map, glossary, tutorial, …).
- **Outside the iframe:** copyable **prompt templates** the user can paste into another
  AI to regenerate or transform the explanation into a representation that suits them.

## Purpose

People understand the same thing differently. One reader wants a table; another wants a
worktree, a FAQ, a sequence, a story, a reading order, or an impact map. The goal of this
skill is to make it easy to convert the *same* understanding target into the
representation that fits *this* reader — and to let the user keep transforming it later on
their own.

## This is not a web app

- No server, no API route, no build pipeline, no chat UI.
- No external CDN, CSS, or JS. The output is a single offline HTML file.
- The iframe never talks to the network and never reaches the parent page.

The final output is **one HTML file** you open directly in a browser.

## Inside vs. outside the iframe

- **Inside the iframe** is the *explanation*. It is sandboxed (`sandbox="allow-scripts"`,
  no `allow-same-origin`), so it cannot touch the parent DOM, storage, or cookies, and it
  cannot make network requests. The representation is chosen per reader — it is not a
  fixed template.
- **Outside the iframe** is *not a chat UI*. It is a set of copyable prompt templates.
  Each is a card with a title, a usage note, the prompt body, and a copy button. The user
  copies one into any AI to get a new representation back.

### Why prompt templates instead of a chat UI

A chat UI would mean network calls, API keys, and state — none of which belong in an
offline, self-contained file. Prompt templates keep the artifact safe and portable while
still letting the user iterate: they choose their own AI, on their own terms, and paste a
ready-made request.

## core.yaml vs. view.yaml

Two intermediate representations sit between the input and the HTML:

| | `core.yaml` | `view.yaml` |
|---|---|---|
| answers | what the target **means** | how to **show** it to this reader |
| depends on the reader? | no | yes |
| contents | concepts, relations, importance, difficulty, confidence, questions, risks, source refs | audience, preferred/avoided forms, density, tone, emphasis, generation policy |
| schema | `references/core-yaml-schema.md` | `references/view-yaml-schema.md` |

Keeping meaning separate from presentation is what lets the user re-target the same
content at a new audience just by changing `view.yaml` — exactly what the "regenerate" and
"iframe-only" prompt templates do.

### Why HTML generation rules instead of a fixed renderer

A fixed renderer would collapse every target into a handful of templates and lose the
whole point — adapting to how a person understands. Instead, an AI generates the iframe UI
freely, guided by `view.yaml` and constrained by **HTML generation rules** (see
`references/html-generation-rules.md`) that keep it safe and self-contained. The Python
scripts only **assemble** and **validate**; they never derive a diagram from `core.yaml`.

## Repository layout

```
adaptive-understanding-html/
  SKILL.md                          entry point + step-by-step procedure
  agents/
    openai.yaml                     portable agent definition for non-Claude runtimes
  scripts/
    build_html.py                   assemble the single HTML (assembler, not renderer)
    validate_html.py                safety / self-containment linter
  references/
    core-yaml-schema.md             meaning structure schema
    view-yaml-schema.md             presentation strategy schema
    html-generation-rules.md        safety + UI rules for generated HTML
    prompt-template-patterns.md     required prompt templates + placeholders
    output-html-structure.md        final two-pane HTML structure
    examples.md                     three worked examples
    sample-core.yaml                sample meaning (a PR)
    sample-view.yaml                sample strategy (engineer)
    sample-iframe.html              sample explanation UI
    sample-prompts.json             sample transform templates
  README.md
```

## scripts/build_html.py

Assembles the outer two-pane shell, embeds the iframe document as a sandboxed `srcdoc`,
renders the prompt templates as copyable cards, and embeds `core.yaml` / `view.yaml` as
viewable metadata. It substitutes `{{core_yaml}}` and `{{view_yaml}}` placeholders in
prompt bodies; any other `{{...}}` token (e.g. `{{希望する表現}}`) is left for the user.

```bash
python scripts/build_html.py \
  --core core.yaml \
  --view view.yaml \
  --iframe iframe.html \
  --prompts prompts.json \
  --output output.html
```

`--iframe`, `--prompts`, `--output` are required; `--core` and `--view` are optional.
(Use `python3` if `python` is not on your PATH. Standard library only — no install.)

## scripts/validate_html.py

Scans a generated HTML file for unsafe or non-self-contained patterns and exits non-zero
if any are found, printing the offending lines.

```bash
python scripts/validate_html.py output.html
```

Detected (each is an error): external `<script src>`, external-loading `<iframe>`,
`<object>`, `<embed>`, external `<link rel="stylesheet">`, `fetch(`, `XMLHttpRequest`,
`WebSocket`, `localStorage`, `sessionStorage`, `document.cookie`, `window.parent`,
`window.top`, `target="_top"`, and any `http://` / `https://` URL. A **required**
sandboxed iframe is not flagged; an iframe that loads an external document is. Pass
`--strict` to also fail on warnings.

## Safety policy of the generated HTML

- Single, offline, self-contained file — no external dependency of any kind.
- The iframe is sandboxed and cannot reach the parent page or the network.
- No storage, no cookies, no secrets, no large verbatim source dumps.
- Verified by `validate_html.py` before delivery.

## Try the sample

```bash
python scripts/build_html.py \
  --core references/sample-core.yaml \
  --view references/sample-view.yaml \
  --iframe references/sample-iframe.html \
  --prompts references/sample-prompts.json \
  --output sample-output.html

python scripts/validate_html.py sample-output.html
```

Open `sample-output.html` in a browser. Right pane: an engineer-oriented PR explanation
(worktree + reading order + review checklist). Left pane: copyable transform templates.

## Usage examples

See `references/examples.md` for three worked examples:

1. Understand a PR as an engineer (worktree + reading order + review checklist).
2. Understand a spec as a PdM (purpose / impact / decision points / risks).
3. Understand a technical doc as a beginner (3 steps + glossary + FAQ).

## Future extensions

- More built-in `view.yaml` presets (designer, SRE, security reviewer, exec summary).
- A small library of reusable iframe layout snippets per form, still AI-composed.
- Optional `--theme` flag for the shell (light / dark / high-contrast).
- A diff mode that highlights what changed between two `core.yaml` versions.
- Export of `core.yaml` / `view.yaml` back out of a generated HTML for round-tripping.
- An optional offline JSON-schema validation step for `core.yaml` / `view.yaml`.
