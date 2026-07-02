# Quiz view rules

Rules for authoring the **interactive quiz view document** — the iframe view that renders
`quiz.yaml` (schema: `../generate-explainer-yaml/references/quiz-yaml-schema.md`) as a
comprehension check: answer → instant grading → explanation. All the general rules in
`html-generation-rules.md` apply (single self-contained document, inline CSS/JS only,
light default + `#theme` hash, no network / storage / frame escape); this file adds the
quiz-specific contract.

The quiz view is a **default view**: author it unless the user explicitly declined a
quiz. If no `quiz.yaml` exists, derive the items yourself from `core.yaml` (concepts →
choice/○×, relations → relation items, `sequence_next`/flows → ordering, risks/questions
→ misconception busters) following the same schema semantics.

## Rendering per question type

- **single_choice / relation** — labelled radio inputs (or buttons) inside a
  `<fieldset>` with the question as `<legend>`. For `relation` items, make the two
  concept labels visually prominent in the question.
- **multiple_choice** — labelled checkboxes in a `<fieldset>` plus an explicit
  「採点する」 button (grading on every toggle is noisy).
- **true_false** — two large ○ / × buttons.
- **ordering** — **no HTML5 drag-and-drop** (poor keyboard/touch accessibility).
  Use click-to-append sequence building (click choices in order, with an undo/やり直す)
  or per-row up/down buttons, then an explicit 「採点する」 button. Every interaction
  must be keyboard-operable.
- Show each item's `difficulty` as a badge (低 / 中 / 高), consistent with how other
  views badge difficulty.

## Grading contract

- Grade **instantly, inside the iframe**, with inline JS only. The answer key is
  embedded in the document (data attributes or a JS object) — never fetched.
- `multiple_choice` = exact **set** match; `ordering` = exact **sequence** match
  (`answer.correct_order`); everything else = the one correct choice id.
- On grading, mark right/wrong visually (color **plus** an icon or text — never color
  alone) and reveal the item's `explanation`, its related concepts, and its
  `source_refs`. Pre-render explanations in hidden elements (`hidden` attribute or a
  collapsed section) — reveal, don't generate.
- After grading, lock the item's inputs (`disabled`) so the score stays honest; the
  「もう一度」 reset restores everything.
- Keep the running score **only in DOM/JS state**. Browser storage is forbidden, so a
  reload resets the quiz — say so visibly in the UI (e.g. 「スコアはこのページ内のみ。
  再読み込みでリセットされます」) so it is not mistaken for a bug.
- End with a score summary (n問中m問正解) and a 「もう一度」 button that resets all
  items and the score.

## Audience adaptation (generation-time, not runtime)

Decide ordering and grouping **when you author the document**, by reading
`view.yaml audience` — do not ship runtime logic that parses YAML:

- **beginner / low familiarity** — order easy → hard; lead with `true_false` and
  `single_choice`; put `relation` / `ordering` items under a 「チャレンジ問題」 section.
- **engineer / advanced** — lead with `relation` / `ordering` and medium+ difficulty;
  easy ○× items can go last or be collapsed.
- Honor `audience_hint.recommended_roles` when present: prioritize matching items, and
  keep non-matching ones reachable (a collapsed 「その他の問題」 section) rather than
  silently dropping them.

## Validator traps (quiz-specific reminders)

- Write the grading JS without forbidden tokens — no fetch-like calls, no browser
  storage, no cookie access, no parent/top access (`validate_html.py` scans raw text,
  including comments and strings).
- Quote sources by `path` (+ lines); never emit an `http://` / `https://` string.
- Keep the standard iframe/theme contract: light default, read your own
  `location.hash` for `#theme=dark` on load and on `hashchange`, palettes via CSS
  variables (`:root` and `:root[data-theme="dark"]`), `prefers-reduced-motion` guard.

See `sample-quiz-iframe.html` for a working document that renders
`../generate-explainer-yaml/references/sample-quiz.yaml` (all five item types) and
passes `validate_html.py --strict`.
