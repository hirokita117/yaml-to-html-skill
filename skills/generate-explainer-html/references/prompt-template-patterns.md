# Prompt template patterns (left-pane content)

The area **outside** the iframe is not a chat UI. It is a set of **copyable prompt
templates** that let the user ask *another* local-file-reading AI to author **one new
iframe view** for the bundle. Each template is a card with a title, a usage description,
the prompt body, a copy button, and optional tags.

`scripts/build_html.py` reads these from a `prompts.json` array and renders the cards into
`index.html`. See `sample-prompts.json` for a working set.

Key rules for this skill:

- Every template produces **one new iframe view document** — never a whole new `index.html`,
  and never an edit to the shell or to other prompts. The deterministic build script is the
  only thing that writes the shell.
- Templates **cite the YAML by absolute path** and tell the AI to read it. They **must not
  embed the YAML content**.
- New views are **additive**: the produced document is saved under `views/` and the bundle
  is rebuilt, adding a switchable tab next to the existing views.

## prompts.json shape

```json
[
  {
    "id": "view-table",
    "title": "テーブルのビューを追加",
    "description": "概念・重要度・難易度・関係・根拠を一覧で見たい人向けのビューを追加する。",
    "tags": ["view", "table"],
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

`build_html.py` substitutes three tokens in each `prompt` with the **absolute path** of
the copied-in YAML files (not their content):

- `{{core_yaml_path}}` → absolute path of `<bundle>/core.yaml`
- `{{view_yaml_path}}` → absolute path of `<bundle>/view.yaml`
- `{{quiz_yaml_path}}` → absolute path of `<bundle>/quiz.yaml`; when the bundle was built
  without `--quiz` and no `quiz.yaml` exists, the token becomes `(quiz.yaml は未指定)` —
  templates that use it should tell the AI to fall back to deriving quiz content from
  `core.yaml` in that case.

Any other `{{...}}` token (for example `{{希望する表現}}`) is **left as-is** so the user
can fill it in before sending. This is how the "free-form" template works.

A template should reference the paths like this and instruct the AI to open them:

```
# 参照（必ず読み込む）
- core.yaml: {{core_yaml_path}}
- view.yaml: {{view_yaml_path}}
- quiz.yaml: {{quiz_yaml_path}}   （クイズ系テンプレートのみ）
これらのファイルを開いてから作ってください。yml の中身はこのプロンプトには貼り付けていません。
```

> The consuming AI is assumed to have **local file access** (Claude Code / Cursor / an
> agentic IDE). A plain web chat that cannot open local files is out of scope by design.

## Safety wording inside prompt bodies

The prompt text is embedded into `index.html` and scanned by `validate_html.py`. Phrase
the "no external dependency" instruction **generically** so you do not write a forbidden
token (e.g. avoid writing `fetch(`, `XMLHttpRequest`, `localStorage`, `document.cookie`,
`window.parent`/`window.top`, or an `http`/`https` URL inside the prompt). Prefer wording
like:

> 制約: <!DOCTYPE html> から始まる単一の自己完結HTML document を出力。外部CDN・外部CSS・
> 外部スクリプト・外部読み込みのiframe を使わない。ネットワーク通信・ブラウザストレージ・
> cookie・親フレームへのアクセスを行わない。

(The substituted absolute paths like `/Users/...` contain no URL scheme, so they do not
trip the validator's `http(s)://` checks.)

## Theme wording inside prompt bodies

Every view document is **light by default** and self-themes from its own URL hash so the
shell's light/dark toggle can reach it across the sandbox boundary. Instruct the AI:

> デフォルトはライトテーマ。URLハッシュ `#theme=dark` を読み取ってダークにも対応する
> （自分の `location.hash` を見て、`hashchange` も listen して `data-theme` を切り替える）。

## Required templates

A generated bundle should include **at least** the following "add a view" templates.
Each one: reads `{{core_yaml_path}}` / `{{view_yaml_path}}`, outputs one self-contained
iframe HTML document (light default + `#theme` hash handling), and states the result is
added as a new switchable view.

1. **Table** — concept list, importance, difficulty, relations, evidence, what to read next.
2. **Worktree** — tree view, directory/file/concept hierarchy, reading order, high-impact
   spots, expandable sections.
3. **Beginner** — term explanations, why it matters, a 3-step path, an analogy, example
   questions.
4. **Engineer** — dependencies, changed files, reading order, review points, risks, tests.
5. **PdM / Biz** — what changes, why it matters, user/business impact, decision points,
   risks and things to confirm.
6. **Quiz** — also reads `{{quiz_yaml_path}}` (falling back to deriving items from
   `core.yaml` when unset); outputs one interactive quiz view (choice / true-false /
   relation / ordering) that grades inline and reveals explanations, adapts order to the
   `view.yaml` audience and per-item difficulty, and states that the score resets on
   reload.
7. **Free-form** — a `{{希望する表現}}` placeholder the user fills in.

> There is intentionally **no "regenerate the whole HTML"** template. The shell and the
> prompts are never rewritten by an AI — only `build_html.py` writes them. To change the
> shell, change the script, not a prompt.

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
(HTML entities resolved), including the substituted absolute YAML paths.
