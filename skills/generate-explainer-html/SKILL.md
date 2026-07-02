---
name: generate-explainer-html
description: turn core.yaml + view.yaml (the explainer's meaning + presentation strategy) — plus quiz.yaml when present — into a self-contained html bundle that helps users understand documents, repositories, pull requests, design notes, or specifications. the bundle has a light/dark shell whose right pane switches between multiple iframe view documents, and copyable prompt templates that ask a local-file-reading ai to add another switchable view. an interactive quiz tab (comprehension check with instant grading) is added by default unless the user explicitly declines. use when the user has (or wants) a core.yaml/view.yaml pair and wants a visual html explainer, or wants to add a new representation (table, worktree, cards, faq, beginner, engineer, pdm view, quiz, …) to an existing bundle. produce the yaml first with the generate-explainer-yaml skill.
---

# generate-explainer-html

Turn a `core.yaml` (meaning) + `view.yaml` (presentation strategy) pair into a
**self-contained HTML bundle** that:

- shows a **tailored explanation UI inside an iframe**, with a **view switcher** in the
  right pane so the reader can flip between multiple representations, and
- offers **copyable prompt templates outside the iframe** so the user can ask another
  local-file-reading AI to **add another switchable view**.

This is the **second half** of the pipeline. The `core.yaml` / `view.yaml` come from the
**`generate-explainer-yaml`** skill (or the user). This skill reads them **by absolute
path**, authors iframe view documents, and assembles the bundle.

```
core.yaml + view.yaml (+ quiz.yaml)  (from generate-explainer-yaml)
  ↓ design + generate (this skill)
HTML bundle: index.html (light/dark shell + view switcher + prompt cards)
             + views/NN-<id>.html  (one switchable iframe view each, incl. a quiz tab)
```

## The bundle (the output)

The output is a **directory**, not a single file:

```
<bundle>/
  index.html          shell: header (theme toggle) + left prompt pane + right view switcher + ONE <iframe>
  views.json          ordered manifest of views {id, label, file}
  core.yaml           copied in (its absolute path is cited by the prompts)
  view.yaml           copied in
  quiz.yaml           copied in when present (comprehension-check questions)
  views/
    01-<id>.html       an iframe view document (full <!DOCTYPE html>, light default)
    02-<id>.html
```

The right-pane iframe loads one view at a time via `src="views/<file>"`; the tab switcher
swaps it. Views are **additive** — each new one becomes another tab; existing views and the
shell/prompts are never rewritten.

Do **not** hand-edit `index.html` or the prompts — `scripts/build_html.py` is their only
author. You author **iframe view documents** only. Do **not** build a web app, server, API,
or chat UI, and do **not** depend on any external CDN/CSS/JS.

## Steps

1. **Get the YAML files.** Take the absolute paths to `core.yaml`, `view.yaml`, and (by
   default) `quiz.yaml` (from the `generate-explainer-yaml` skill, or the user). **Read
   them.** If they don't exist yet, produce them with `generate-explainer-yaml` first.

2. **Author one iframe view document** — a full `<!DOCTYPE html>` document tailored to the
   target and reader. Choose the form(s) from `view.yaml` (table, worktree, cards, faq,
   comparison, sequence, reading path, risk/dependency/impact map, glossary, tutorial,
   review checklist, …). It must include source references, important concepts, relations,
   what to read next, and next questions, and have real visual structure. It must be **light
   by default** and read `#theme` from its own URL hash (load + `hashchange`). Inline
   CSS/JS only; no network. Follow `references/html-generation-rules.md`. Example:
   `references/sample-iframe.html`.

3. **Author the quiz view document (default — skip only on explicit opt-out).** Unless
   the user explicitly declined a quiz, also author an interactive quiz view from
   `quiz.yaml` (or, if no `quiz.yaml` exists, derive items from `core.yaml`): answer →
   instant grading → explanation, order adapted to the `view.yaml` audience and per-item
   difficulty. Rules: `references/quiz-view-rules.md`. Example:
   `references/sample-quiz-iframe.html`.

4. **Author the prompt templates** as a `prompts.json` array — the "add a view" cards
   (table, worktree, beginner, engineer, PdM/Biz, quiz, free-form). Each cites the YAML
   via `{{core_yaml_path}}` / `{{view_yaml_path}}` (the quiz card also
   `{{quiz_yaml_path}}`) and **must not** embed YAML content. Patterns:
   `references/prompt-template-patterns.md`. Starter set: `references/sample-prompts.json`.

5. **Build the bundle** with `scripts/build_html.py` (see below). Pass `--core` / `--view`
   / `--quiz` (copied in; their absolute paths feed the prompt placeholders) and one or
   more `--view-html "ラベル=その.html"` — including the quiz view, e.g.
   `--view-html "クイズ=quiz.html"`.

6. **Validate** the bundle with `scripts/validate_html.py` on `index.html` **and** every
   `views/*.html`. Fix any error and re-validate until it exits 0.

7. **Hand the user the bundle folder** with open instructions (below). Summarize which views
   exist and which "add a view" templates are available.

## Adding a view later (the additive flow)

To add a representation next to the existing ones — **do not overwrite**:

1. Author one more iframe view document (or have a local-file-reading AI do it via a copied
   prompt — those prompts already say "read the YAML at the given path; return one new view").
2. Re-run the build with **only the new view**:
   ```bash
   python scripts/build_html.py --bundle <dir> --prompts <prompts.json> \
     --view-html "テーブル=table.html"
   ```
   It **appends** the view to `views.json` and regenerates `index.html` with a new tab. The
   existing views, the shell, and the prompts are preserved. (Re-running with an existing
   label updates that view in place instead of duplicating it.)

## Using the scripts

> Note: invoke with `python3` if `python` is not on PATH.

Build / grow the bundle:

```bash
python scripts/build_html.py \
  --bundle ./explainer-bundle \
  --core /abs/path/core.yaml \
  --view /abs/path/view.yaml \
  --quiz /abs/path/quiz.yaml \
  --prompts prompts.json \
  --view-html "エンジニア=engineer.html" \
  --view-html "クイズ=quiz.html"
```

`--bundle` and `--prompts` are required; `--core` / `--view` / `--quiz` are optional
(recommended — the prompts cite their absolute path) and are left in place on a re-run if
omitted; `--view-html` is repeatable and appends/updates views.

Validate (safety / self-containment check), including every view file:

```bash
python scripts/validate_html.py ./explainer-bundle/index.html ./explainer-bundle/views/*.html
```

`build_html.py` is an **assembler**, not a renderer: it never turns `core.yaml` into a fixed
diagram. The understanding UI is the iframe view document(s) you authored in step 2.

## Opening the bundle

- **Chrome/Edge block `file://` iframe loads.** Open `index.html` in **Firefox** over
  `file://`, or serve the folder with a trivial local static server (e.g.
  `python3 -m http.server` run **inside the bundle dir** — it reads only local files; the
  no-network rule constrains the *content*, not how you serve the folder).
- The right-pane tabs switch views; the header toggle flips light/dark for the shell and
  propagates the theme into the iframe via the `#theme` hash.

## Troubleshooting

- **`validate_html.py` fails on an `http://` / `https://` string** — a URL leaked into a
  `source_ref` or a prompt body. URLs are labels here, not live links: drop the scheme
  (write `example.com/path`) or remove the URL, then re-validate.
- **`validate_html.py` fails on `fetch(` / `XMLHttpRequest` / `localStorage` / etc.** — the
  forbidden token appears literally inside a prompt body or a view. Reword it generically;
  see `references/prompt-template-patterns.md` → "Safety wording inside prompt bodies".
- **Iframe is blank in Chrome over `file://`** — expected; use Firefox or serve the folder.
- **`build_html.py: --view-html must be "LABEL=PATH"`** — pass each view as `ラベル=パス`.
- **`build_html.py: no views to build`** — pass at least one `--view-html`, or build into a
  bundle that already has a `views.json`.
- **A view tab 404s** — its `views/NN-*.html` was removed; rebuild it with `--view-html`.
- **Empty or trivial input** — if there is no real target to explain, ask the user for the
  actual document / repo / PR and produce the YAML first; do not emit an empty explainer.

## Try it with the bundled sample

```bash
python scripts/build_html.py \
  --bundle ./sample-bundle \
  --core ../generate-explainer-yaml/references/sample-core.yaml \
  --view ../generate-explainer-yaml/references/sample-view.yaml \
  --quiz ../generate-explainer-yaml/references/sample-quiz.yaml \
  --prompts references/sample-prompts.json \
  --view-html "エンジニア=references/sample-iframe.html" \
  --view-html "クイズ=references/sample-quiz-iframe.html"

python scripts/validate_html.py ./sample-bundle/index.html ./sample-bundle/views/*.html
```

Open `sample-bundle/index.html` (Firefox / served). The right pane shows an
engineer-oriented PR explanation (worktree + reading order + review checklist) plus an
interactive quiz tab; the left pane has the copyable "add a view" templates and the YAML
viewers.

## Reference material

- `references/html-generation-rules.md` — safety + UI rules for view documents (src-loaded
  iframe, light default, `#theme` hash)
- `references/quiz-view-rules.md` — rules for the interactive quiz view (per-type
  rendering, grading contract, audience adaptation)
- `references/output-bundle-structure.md` — the bundle's structure and shell
- `references/prompt-template-patterns.md` — "add a view" prompt templates + path placeholders
- `references/sample-iframe.html` — sample iframe view (engineer)
- `references/sample-quiz-iframe.html` — sample interactive quiz view
- `references/sample-prompts.json` — sample "add a view" templates
- `references/examples.md` — three worked reader views
- `agents/openai.yaml` — portable description of this skill for non-Claude agents
- YAML schema (produced by the sibling skill): `../generate-explainer-yaml/references/`
  (`core-yaml-schema.md`, `view-yaml-schema.md`, `quiz-yaml-schema.md`)
