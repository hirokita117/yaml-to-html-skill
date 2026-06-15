# yaml-to-html explainer

[![License: MIT](https://img.shields.io/github/license/hirokita117/yaml-to-html-skill)](LICENSE)
[![Latest release](https://img.shields.io/github/v/release/hirokita117/yaml-to-html-skill)](https://github.com/hirokita117/yaml-to-html-skill/releases)
[![Claude Code plugin](https://img.shields.io/badge/Claude%20Code-plugin-6E56CF)](#install-as-a-claude-code-plugin)

A Claude Code plugin with **two skills** that turn an **understanding target** — a
document, repository summary, pull request / diff, README, design note, or specification —
into an **offline HTML explainer bundle** tailored to how a particular reader understands
things.

The two skills split the work cleanly:

| skill | role | output |
|---|---|---|
| **`generate-explainer-yaml`** | Gen YAML | `core.yaml` (meaning) + `view.yaml` (presentation strategy) |
| **`generate-explainer-html`** | Gen HTML | a bundle: a light/dark shell + switchable iframe views |

```
Input (doc / repo / PR / README / design note / spec)
  ↓ generate-explainer-yaml
core.yaml  (what it MEANS — concepts, relations, importance, difficulty, sources)
view.yaml  (how to SHOW it to this reader — audience, forms, emphasis)
  ↓ generate-explainer-html
HTML bundle: index.html (light/dark shell + view switcher + add-a-view prompts)
             + views/NN-<id>.html  (one switchable iframe view each)
```

## Quick start

**1. Install the plugin** (run these inside Claude Code):

```
/plugin marketplace add hirokita117/yaml-to-html-skill
/plugin install yaml-to-html@yaml-to-html-skill
```

**2. Ask for an explainer.** A single prompt runs **both** skills in the right order —
`generate-explainer-yaml` first (writes `core.yaml` + `view.yaml`), then
`generate-explainer-html` (reads that YAML by absolute path and builds the HTML bundle).
Paste a document / repo summary / PR diff / README / design note, or point at a path.

**English**

```
Build me an offline HTML explainer bundle for this PR, aimed at an engineer reviewing it.
First use generate-explainer-yaml to produce core.yaml + view.yaml, then use
generate-explainer-html to turn that YAML (by absolute path) into a light/dark switchable
view bundle in ./explainer-bundle.

--- target ---
<paste the PR / document / repo summary / README / design note here, or give a path>
```

**Japanese**

```
この PR を、レビューするエンジニア向けに分かりやすく説明する HTML バンドルを作ってください。
まず generate-explainer-yaml で core.yaml と view.yaml を生成し、
続けて generate-explainer-html でその YAML（絶対パス）から
ライト/ダーク切り替え付きのビュー HTML バンドルを ./explainer-bundle に組み立ててください。

--- 対象 ---
<ここに PR / ドキュメント / リポジトリ概要 / README / 設計メモを貼る、またはパスを指定>
```

**3. Open it.** Open `./explainer-bundle/index.html` in **Firefox** over `file://`, or serve
the folder for Chrome/Edge (`cd explainer-bundle && python3 -m http.server`). See
[Opening the bundle](#opening-the-bundle-browser-note) for why.

> Prefer to drive it step by step? Generate just the YAML first ("`generate-explainer-yaml で
> core.yaml と view.yaml を作って`"), review the two files, then hand their absolute paths to
> `generate-explainer-html`.

## What the output looks like

The HTML output is a **bundle (a directory)**, not a single file:

- **A light/dark shell** (`index.html`) with a theme toggle (light by default).
- **A right pane that switches between iframe views.** Each view is a separate
  self-contained HTML document under `views/`. Views are **additive** — ask for a "table"
  view next to your "beginner" view and you get a second tab, not a replacement.
- **A left pane of copyable prompt templates.** Each asks another *local-file-reading* AI
  (Claude Code / Cursor / an agentic IDE) to read the YAML **by absolute path** and return
  **one new view** to add to the bundle. The prompts never embed the YAML content.

## This is not a web app

- No server, no API route, no build pipeline, no chat UI.
- No external CDN, CSS, or JS; no network calls; no storage or cookies.
- Each view runs in a sandboxed iframe (`sandbox="allow-scripts"`, no `allow-same-origin`)
  and cannot reach the parent page.

The shell loads each view via a **local relative `src`** (e.g. `views/01-engineer.html`) —
a local file read, not a network read. (A remote `src` stays forbidden.)

## core.yaml vs. view.yaml

Two intermediate representations sit between the input and the HTML, produced by
`generate-explainer-yaml`:

| | `core.yaml` | `view.yaml` |
|---|---|---|
| answers | what the target **means** | how to **show** it to this reader |
| depends on the reader? | no | yes |
| contents | concepts, relations, importance, difficulty, confidence, questions, risks, source refs | audience, preferred/avoided forms, density, tone, emphasis, generation policy |
| schema | `generate-explainer-yaml/references/core-yaml-schema.md` | `generate-explainer-yaml/references/view-yaml-schema.md` |

Keeping meaning separate from presentation is what lets the same `core.yaml` become many
switchable views — each a different *form* of the same meaning.

## Install as a Claude Code plugin

The [Quick start](#quick-start) lists the two install commands. Once installed, both skills
are available to Claude as `generate-explainer-yaml` and `generate-explainer-html`
(namespaced `yaml-to-html:generate-explainer-html`, etc.). You can also use the scripts
directly from a clone without installing the plugin.

## Updating the plugin

When this skill is updated and the `version` in `.claude-plugin/plugin.json` (and
`marketplace.json`) is bumped, users who installed via the marketplace need to update to get
the new version. The installed copy does **not** update itself automatically by default.

Run these inside Claude Code:

```
/plugin marketplace update yaml-to-html-skill
/plugin install yaml-to-html@yaml-to-html-skill
/reload-plugins
```

1. **`/plugin marketplace update yaml-to-html-skill`** — re-fetches the latest
   `marketplace.json` from the repo so Claude Code sees the new version. This step is a
   **required prerequisite**: without it, the install command below won't see the update.
2. **`/plugin install yaml-to-html@yaml-to-html-skill`** — re-running install pulls in the
   new version.
3. **`/reload-plugins`** — activates the updated skill content in the current session
   without a full restart. (Restarting Claude Code also works.)

> **Tip — enable auto-update.** To skip these steps in future, run `/plugin`, open the
> **Marketplaces** tab, select `yaml-to-html-skill`, and toggle **Enable auto-update**.
> Claude Code will then refresh the marketplace and update the plugin at startup.

To confirm which version you have, run `/plugin`, open the **Plugins** (or **Installed**)
tab, and check the version shown for `yaml-to-html` against the `version` in
[`.claude-plugin/plugin.json`](.claude-plugin/plugin.json).

## Repository layout

```
yaml-to-html-skill/
  README.md                         this file — repository overview
  LICENSE                           MIT license
  .claude-plugin/
    plugin.json                     plugin manifest (name, version, metadata)
    marketplace.json                marketplace manifest (lets users add+install this repo)
  skills/
    generate-explainer-yaml/        Skill A — Gen YAML
      SKILL.md                      entry point + procedure
      agents/openai.yaml            portable agent definition
      references/
        core-yaml-schema.md         meaning structure schema (core/v1)
        view-yaml-schema.md         presentation strategy schema (view/v1)
        sample-core.yaml            sample meaning (a PR)
        sample-view.yaml            sample strategy (engineer)
        examples.md                 three worked intents
    generate-explainer-html/        Skill B — Gen HTML
      SKILL.md                      entry point + procedure
      agents/openai.yaml            portable agent definition
      scripts/
        build_html.py               build/grow the bundle (assembler, not renderer)
        validate_html.py            safety / self-containment linter
      references/
        html-generation-rules.md    safety + UI rules for view documents
        output-bundle-structure.md  the bundle's structure and shell
        prompt-template-patterns.md add-a-view prompt templates + path placeholders
        sample-iframe.html          sample iframe view (engineer)
        sample-prompts.json         sample add-a-view templates
        examples.md                 three worked bundles
```

## scripts/build_html.py

Builds and **grows** a bundle: writes the shell (`index.html`), merges views into
`views.json`, copies `core.yaml` / `view.yaml` in, and renders the prompt cards. It
substitutes `{{core_yaml_path}}` / `{{view_yaml_path}}` (the **absolute paths** of the
copied-in YAML) into prompt bodies; any other `{{...}}` token (e.g. `{{希望する表現}}`) is
left for the user.

```bash
# from skills/generate-explainer-html/
python scripts/build_html.py \
  --bundle ./explainer-bundle \
  --core /abs/path/core.yaml \
  --view /abs/path/view.yaml \
  --prompts references/sample-prompts.json \
  --view-html "エンジニア=references/sample-iframe.html"
```

`--bundle` and `--prompts` are required; `--core` / `--view` are optional (recommended);
`--view-html "LABEL=PATH"` is repeatable. Re-running with a new `--view-html` **appends** a
view; re-running an existing label **updates it in place**. (Use `python3` if `python` is
not on your PATH. Standard library only — no install.)

## scripts/validate_html.py

Scans the bundle for unsafe or non-self-contained patterns and exits non-zero if any are
found, printing the offending lines. Pass `index.html` and every view file:

```bash
python scripts/validate_html.py ./explainer-bundle/index.html ./explainer-bundle/views/*.html
```

Detected (each is an error): external `<script src>`, remote-loading `<iframe>` (scheme
`://` or `//`), `<object>`, `<embed>`, external `<link rel="stylesheet">`, `fetch(`,
`XMLHttpRequest`, `WebSocket`, `localStorage`, `sessionStorage`, `document.cookie`,
`window.parent`, `window.top`, `target="_top"`, and any `http://` / `https://` URL. A
**local relative** iframe `src` (into `views/`) is allowed. Pass `--strict` to also fail on
warnings.

## Opening the bundle (browser note)

Because each view loads via an `iframe src`, **Chrome/Edge block `file://` iframe loads**
("Not allowed to load local resource"). Open the bundle either:

- in **Firefox** over `file://`, or
- by serving the folder with a trivial static server, e.g. `python3 -m http.server` run
  **inside the bundle dir** — that reads only local files; the no-network rule constrains
  the *content*, not how you serve the folder.

## Safety policy of the generated bundle

- Offline, self-contained bundle — no external dependency of any kind.
- Each view is sandboxed and cannot reach the parent page or the network.
- No storage, no cookies, no secrets, no large verbatim source dumps.
- Verified by `validate_html.py` before delivery.

## Try the sample

```bash
# from skills/generate-explainer-html/
python scripts/build_html.py \
  --bundle ./sample-bundle \
  --core ../generate-explainer-yaml/references/sample-core.yaml \
  --view ../generate-explainer-yaml/references/sample-view.yaml \
  --prompts references/sample-prompts.json \
  --view-html "エンジニア=references/sample-iframe.html"

python scripts/validate_html.py ./sample-bundle/index.html ./sample-bundle/views/*.html
```

Open `sample-bundle/index.html` (Firefox / served). Right pane: an engineer-oriented PR
explanation (worktree + reading order + review checklist), with a light/dark toggle and a
view switcher. Left pane: copyable "add a view" templates and the YAML viewers.

## Usage examples

- `skills/generate-explainer-yaml/references/examples.md` — three worked YAML intents.
- `skills/generate-explainer-html/references/examples.md` — three worked bundles, including
  how to **add** a second view next to the first.

## Future extensions

- More built-in `view.yaml` presets (designer, SRE, security reviewer, exec summary).
- A small library of reusable iframe view snippets per form, still AI-composed.
- A diff mode that highlights what changed between two `core.yaml` versions.
- Export of `core.yaml` / `view.yaml` back out of a bundle for round-tripping.
- An optional offline JSON-schema validation step for `core.yaml` / `view.yaml`.
