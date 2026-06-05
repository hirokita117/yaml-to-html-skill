---
name: generate-explainer-html
description: generate a single self-contained html file that helps users understand documents, repositories, pull requests, design notes, or specifications through personalized visual explanations. use when the user wants an html output with an iframe-based explanation area and copyable prompt templates for asking another ai to regenerate or transform the explanation into tables, worktrees, cards, faq, comparison views, sequence views, story views, or other user-friendly representations.
---

# generate-explainer-html

Turn an understanding target — a pasted document, repository summary, PR/diff summary,
README, design note, or spec — into **one self-contained HTML file** that:

- shows a **tailored explanation UI inside an iframe**, and
- offers **copyable prompt templates outside the iframe** so the user can ask another AI
  to regenerate the explanation in whatever representation suits them.

This skill's center is **not** a fixed renderer. It is:

1. `core.yaml` — the semantic structure of the target (meaning, not UI)
2. `view.yaml` — how to present it to this particular reader
3. flexible iframe HTML generated from those, following the generation rules
4. prompt templates that let the user re-generate / transform / drill in later

Do **not** build a web app, server, API route, or chat UI. Do **not** collapse into a few
fixed templates. Do **not** depend on any external CDN/CSS/JS. The output is offline.

## Flow

```
Input (document / repo summary / PR diff / README / design doc / any technical text)
  ↓ analyze
core.yaml   (concepts, relations, importance, difficulty, evidence, source refs)
  ↓ view strategy
view.yaml   (audience, preferred/avoided forms, density, emphasis)
  ↓ generate
single HTML (iframe = explanation UI; outside iframe = prompt templates)
```

## Steps to run this skill

1. **Read the input.** Take whatever the user pasted or pointed at. Identify the target
   type (document / repository / pull_request / design_note / spec).

2. **Create `core.yaml` if useful.** Capture the *meaning*: concepts (with importance,
   difficulty, confidence), relations, questions, risks, and `source_refs`. Keep it
   compact — compress to what matters; do not transcribe the source. Schema:
   `references/core-yaml-schema.md`. Skip a written file only for tiny inputs, but still
   reason in these terms.

3. **Create `view.yaml` if useful.** Decide how to present it to *this* reader: audience
   role/familiarity, preferred and avoided forms, density, tone, what to emphasize, and
   the `html_generation_policy`. If the user did not say, infer a sensible strategy and
   **state the assumption**. Schema: `references/view-yaml-schema.md`.

4. **Generate the iframe HTML** — a full `<!DOCTYPE html>` document tailored to the target
   and reader. Choose the form(s) from `view.yaml` (table, worktree, cards, faq,
   comparison, sequence, timeline, reading path, risk/dependency/impact map, glossary,
   tutorial, review checklist, decision map, …). It must include source references,
   important concepts, relations, what to read next, and next questions to ask an AI, and
   have real visual structure (not flat prose). Follow `references/html-generation-rules.md`
   and `references/output-html-structure.md`. Inline CSS/JS only; no network.

5. **Generate the prompt templates** (outside the iframe) as a `prompts.json` array. Include
   at least: regenerate-full, iframe-only, table, worktree, beginner, engineer, PdM/Biz,
   and a free-form `{{希望する表現}}` template. Use `{{core_yaml}}` / `{{view_yaml}}`
   placeholders where the prompt should carry the structured context. Patterns:
   `references/prompt-template-patterns.md`.

6. **Assemble the single HTML** with `scripts/build_html.py` (see below). This wraps the
   iframe document and the prompt cards in the two-pane shell and embeds the YAML as
   viewable metadata.

7. **Validate** with `scripts/validate_html.py`. It checks for unsafe / non-self-contained
   patterns and exits non-zero on any error.

8. **Fix and re-validate** until `scripts/validate_html.py` exits 0 (no errors). Only then
   hand the user a file that opens directly in a browser with no network access. Summarize
   what is inside the iframe and which transform templates are available outside it.

## Using the scripts

> Note: invoke with `python3` if `python` is not on PATH.

Build (assemble the single HTML):

```bash
python scripts/build_html.py \
  --core core.yaml \
  --view view.yaml \
  --iframe iframe.html \
  --prompts prompts.json \
  --output output.html
```

`--iframe`, `--prompts`, and `--output` are required; `--core` and `--view` are optional
(omit them for tiny inputs — they are embedded as metadata and substituted into prompt
placeholders when present).

Validate (safety / self-containment check):

```bash
python scripts/validate_html.py output.html
```

`build_html.py` is an **assembler**, not a renderer: it never turns `core.yaml` into a
fixed diagram. The understanding UI is the iframe document you authored in step 4.

## Troubleshooting

- **`validate_html.py` fails on an `http://` / `https://` string** — a URL leaked into a
  `source_ref` or a prompt body. URLs are labels here, not live links: drop the scheme
  (write `example.com/path`) or remove the URL, then re-validate.
- **`validate_html.py` fails on `fetch(` / `XMLHttpRequest` / `localStorage` / etc.** — the
  forbidden token appears literally inside a prompt body. Reword it generically; see
  `references/prompt-template-patterns.md` → "Safety wording inside prompt bodies".
- **`build_html.py: input file not found`** — check the `--iframe` / `--prompts` / `--core`
  / `--view` paths.
- **`build_html.py: could not parse prompts JSON`** — `prompts.json` must be a JSON array of
  objects (see `references/prompt-template-patterns.md`).
- **Loop / exit condition** — repeat step 8 (fix → re-validate) until `validate_html.py`
  exits 0. Only then hand the file to the user.
- **Empty or trivial input** — if there is no real target to explain, ask the user for the
  actual document / repo / PR first; do not emit an empty explainer.

## Try it with the bundled sample

```bash
python scripts/build_html.py \
  --core references/sample-core.yaml \
  --view references/sample-view.yaml \
  --iframe references/sample-iframe.html \
  --prompts references/sample-prompts.json \
  --output sample-output.html

python scripts/validate_html.py sample-output.html
```

Open `sample-output.html` in a browser. The right pane shows an engineer-oriented PR
explanation (worktree + reading order + review checklist); the left pane has the
copyable transform templates.

## Examples

Three worked end-to-end examples (engineer PR / PdM spec / beginner doc), each showing the
input, the `core.yaml` / `view.yaml` intent, and the inside-vs-outside-iframe split, live in
`references/examples.md`. The bundled sample implements Example 1.

## Reference material

- `references/core-yaml-schema.md` — meaning structure schema
- `references/view-yaml-schema.md` — presentation strategy schema
- `references/html-generation-rules.md` — safety + UI rules for generated HTML
- `references/prompt-template-patterns.md` — required prompt templates + placeholders
- `references/output-html-structure.md` — final two-pane HTML structure
- `references/examples.md` — three worked examples (engineer / PdM / beginner)
- `agents/openai.yaml` — portable description of this skill for non-Claude agents
