# Examples — core.yaml / view.yaml intent

Three worked intents for this skill. Each shows the input and the `core.yaml` (meaning) +
`view.yaml` (strategy) you would author. The bundled `sample-core.yaml` / `sample-view.yaml`
implement **Example 1**.

The point across all three: the `core.yaml` (meaning) can stay largely the same; swapping
`view.yaml` (strategy) is what re-targets the explanation at a different reader. That is
exactly what the downstream `generate-explainer-html` skill exploits when it adds new views.

---

## Example 1 — Understand a PR as an engineer

**Input:** PR summary ("Add rate limiting to the public API"), changed files
(`rate_limit.py`, `token_bucket.py`, `rate_limits.yaml`, tests), diff summary.

**core.yaml (meaning)**
- concepts: `RateLimitMiddleware` (high), `TokenBucketStore` (high, difficult), per-route
  config (medium), tests (medium)
- relations: middleware `depends_on` store and config; tests `explains` middleware
- risks: per-process limits (high), unbounded bucket growth (medium)
- questions: multi-instance behavior, client-key spoofing

**view.yaml (strategy)**
- role `engineer`, familiarity `intermediate`
- preferred forms: `worktree`, `reading_path`, `review_checklist`; dislikes: `dense_table`
- emphasize: dependencies, reading order, impact, risks

---

## Example 2 — Understand a spec as a PdM

**Input:** the specification document body.

**core.yaml (meaning)**
- concepts framed as decisions, requirements, and impacts rather than modules
- importance keyed to business impact; risks captured explicitly
- `source_refs` point at sections of the spec

**view.yaml (strategy)**
- role `product_manager` / `business`, familiarity `intermediate`
- preferred forms: `impact_map`, `decision_map`, `faq`; avoid: `dense_table`
- emphasize: purpose, impact, decision points, risks; de-emphasize: implementation detail

---

## Example 3 — Understand a technical doc as a beginner

**Input:** a technical document.

**core.yaml (meaning)**
- concepts tagged with `difficulty` so hard terms are visible
- a glossary's worth of term definitions captured as concept `detail`
- low-confidence items surfaced as `questions`

**view.yaml (strategy)**
- role `beginner`, familiarity `beginner`
- preferred forms: `beginner_tutorial`, `glossary`, `faq`
- tone `tutorial`, density `low`, interaction_level `medium`
- emphasize: why it matters, step-by-step path

---

## Pattern across all three

| | Example 1 | Example 2 | Example 3 |
|---|---|---|---|
| reader | engineer | PdM / Biz | beginner |
| emphasize | dependencies, risks | impact, decisions | why-it-matters, steps |
| forms in view.yaml | worktree + reading order + review checklist | impact / decision maps + faq | 3-step tutorial + glossary + faq |

After authoring the pair, hand the absolute paths to `generate-explainer-html` to build the
HTML bundle, where each reader's strategy becomes a switchable view.
