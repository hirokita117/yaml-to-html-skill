# Output HTML structure

The final artifact is a **single self-contained HTML file** that opens directly in a
browser with no network access. It has two roles, split into two panes:

- **Left pane** — copyable prompt templates + `core.yaml` / `view.yaml` viewers + help.
- **Right pane** — an iframe whose content is the explanation UI for the target.

## Skeleton

```text
<html>
  <head>
    inline <style>            (no external CSS)
  </head>
  <body>
    app shell
      header                  (title + subtitle / source label)
      main layout (2 panes)
        left  pane: prompt templates panel
                    core.yaml / view.yaml viewers (tabbed)
                    help / usage
        right pane: iframe preview (the explanation UI)
      optional metadata panel
      optional source references panel
    inline <script>           (copy buttons, tab switching; no external JS)
  </body>
</html>
```

`scripts/build_html.py` produces exactly this shape. It is an **assembler**: it places
the AI-authored iframe document and prompt templates into the shell; it does not derive a
fixed diagram from `core.yaml`.

## Layout / UX requirements

- Two panes side by side on wide screens.
- Stacks vertically on narrow / mobile screens (single column).
- No external dependency; everything inline.
- Respects `prefers-reduced-motion`.
- Keyboard operable; visible focus styles; labelled controls.

```text
左ペイン:                          右ペイン:
  - プロンプトテンプレート集          - iframe preview
  - 表現変換テンプレート              - iframe内に図解UI
  - コピーボタン
  - core.yaml / view.yaml 表示切替
  - 使い方
```

## The iframe (right pane)

- Holds a **full HTML document** tailored to the target and the reader.
- Embedded with `srcdoc` and `sandbox="allow-scripts"` (never `allow-same-origin`).
- The representation is **not fixed** — table, worktree, cards, faq, comparison,
  sequence, timeline, reading path, risk map, dependency map, glossary, beginner
  tutorial, review checklist, decision map, impact map, or combinations.
- Must include: source references, important concepts, relations, what to read next,
  next questions to ask an AI. Must have visual structure, not flat prose.

## The prompt templates (left pane)

- Not a chat UI. A set of cards the user copies into another AI.
- Each card: title, usage description, prompt body (collapsible), copy button, optional
  tags.
- Copy button: clipboard API with a textarea-select fallback.
- See `prompt-template-patterns.md` for the required set and `sample-prompts.json` for a
  working example.

## Metadata viewers (left pane)

- `core.yaml` and `view.yaml` are embedded as read-only text, toggled by tabs.
- They make the output self-explanatory and feed the "regenerate" prompts (which inline
  the same YAML via `{{core_yaml}}` / `{{view_yaml}}` placeholders).

## Safety properties of the output

- No network requests, no external scripts/CSS/iframes, no storage, no cookies.
- The iframe cannot reach the parent page (no `allow-same-origin`).
- Verified by `scripts/validate_html.py` (see `html-generation-rules.md`).
