# Examples — building and growing a view bundle

Three worked examples of this skill. Each starts from a `core.yaml` / `view.yaml` pair
(produced by the `generate-explainer-yaml` skill) and shows what goes **inside a view**, how
to **build the bundle**, and how to **add another switchable view** later.

The bundled sample (`sample-iframe.html`, `sample-prompts.json`) plus the sibling skill's
`sample-core.yaml` / `sample-view.yaml` implement **Example 1**.

---

## Example 1 — A PR for an engineer, then add a table view

**YAML in:** engineer strategy (`worktree` + `reading_path` + `review_checklist`),
emphasize dependencies / reading order / risks.

**Inside the first view (`views/01-engineer.html`)**
- worktree of the changed files with a reading-order number on each, high-impact flagged
- concept cards with importance / difficulty / confidence badges
- relations, a "what to read next" path, a review checklist
- risks and "next questions to ask an AI"
- light by default; reads `#theme` for dark

**Build the bundle**
```bash
python scripts/build_html.py \
  --bundle ./explainer-bundle \
  --core /abs/core.yaml --view /abs/view.yaml \
  --prompts references/sample-prompts.json \
  --view-html "エンジニア=views-src/engineer.html"
python scripts/validate_html.py ./explainer-bundle/index.html ./explainer-bundle/views/*.html
```

**Add a table view later (additive — the engineer view stays)**
```bash
python scripts/build_html.py --bundle ./explainer-bundle \
  --prompts references/sample-prompts.json \
  --view-html "テーブル=views-src/table.html"
```
Now the right pane has two tabs — エンジニア / テーブル — switchable.

---

## Example 2 — A spec for a PdM, then add an FAQ view

**YAML in:** product/business strategy (`impact_map` + `decision_map` + `faq`), emphasize
purpose / impact / decisions / risks; de-emphasize implementation detail.

**Inside the first view**
- purpose / impact / decision points / risks, grouped visually
- "what changes and why it matters", user impact and business impact
- decision points and things to confirm, next questions

**Then add** a `faq` view (`--view-html "FAQ=views-src/faq.html"`) next to the PdM view —
copy the **free-form** prompt card, tell a local-file-reading AI "FAQ 形式で", save the
returned document, and re-run the build.

---

## Example 3 — A doc for a beginner, then add a glossary view

**YAML in:** beginner strategy (`beginner_tutorial` + `glossary` + `faq`), tone `tutorial`,
density `low`, emphasize why-it-matters and a step-by-step path.

**Inside the first view**
- a 3-step path to understanding, an analogy for the hardest concept
- a glossary of terms with short plain explanations, a FAQ, next questions

**Then add** a dedicated `glossary` view next to the tutorial view via the free-form card.

---

## Pattern across all three

Same machinery, different `view.yaml` and different *views in the same bundle*:

| | Example 1 | Example 2 | Example 3 |
|---|---|---|---|
| reader | engineer | PdM / Biz | beginner |
| first view | worktree + reading order + review checklist | purpose / impact / decisions / risks | 3 steps + glossary + FAQ |
| added view | table | faq | glossary |

The `core.yaml` (meaning) stays the same across views; each view is a different *form* of
it. New forms are **added** as switchable tabs — the reader keeps the old view and gains the
new one, instead of overwriting. That is exactly what the left-pane "add a view" prompt
templates let the user do later, on their own, with another local-file-reading AI.
