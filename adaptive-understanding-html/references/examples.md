# Examples

Three worked examples of using the skill. Each shows the input, the `core.yaml` /
`view.yaml` intent, what goes **inside** the iframe, and what goes **outside** it.

The bundled sample data (`sample-core.yaml`, `sample-view.yaml`, `sample-iframe.html`,
`sample-prompts.json`) implements **Example 1**.

---

## Example 1 — Understand a PR as an engineer

**Input**
- PR summary ("Add rate limiting to the public API")
- changed files (`rate_limit.py`, `token_bucket.py`, `rate_limits.yaml`, tests)
- diff summary

**core.yaml (intent)**
- concepts: `RateLimitMiddleware` (high), `TokenBucketStore` (high, difficult),
  per-route config (medium), tests (medium)
- relations: middleware `depends_on` store and config; tests `explains` middleware
- risks: per-process limits (high), unbounded bucket growth (medium)
- questions: multi-instance behavior, client-key spoofing

**view.yaml (strategy)**
- role `engineer`, familiarity `intermediate`
- preferred forms: `worktree`, `reading_path`, `review_checklist`
- dislikes: `dense_table`
- emphasize: dependencies, reading order, impact, risks

**Inside the iframe**
- worktree of the changed files with a reading-order number on each
- high-impact files flagged
- concept cards with importance / difficulty / confidence badges
- relations between concepts
- "what to read next" path
- a review checklist
- risks and "next questions to ask an AI"

**Outside the iframe (prompt templates)**
- engineer-focused transform
- table transform
- "add more review angles" (free-form)
- regenerate-full / iframe-only

> Reproduce it:
> ```bash
> python scripts/build_html.py \
>   --core references/sample-core.yaml \
>   --view references/sample-view.yaml \
>   --iframe references/sample-iframe.html \
>   --prompts references/sample-prompts.json \
>   --output sample-output.html
> python scripts/validate_html.py sample-output.html
> ```

---

## Example 2 — Understand a spec as a PdM

**Input**
- the specification document body

**core.yaml (intent)**
- concepts framed as decisions, requirements, and impacts rather than modules
- importance keyed to business impact; risks captured explicitly
- source_refs point at sections of the spec

**view.yaml (strategy)**
- role `product_manager` / `business`, familiarity `intermediate`
- preferred forms: `impact_map`, `decision_map`, `faq`
- avoid forms: `dense_table`
- emphasize: purpose, impact, decision points, risks
- de-emphasize: implementation detail

**Inside the iframe**
- purpose / impact / decision points / risks, grouped visually
- "what changes and why it matters"
- user impact and business impact
- decision points and things to confirm
- next questions to ask an AI

**Outside the iframe (prompt templates)**
- PdM / Biz transform
- "turn this into an FAQ" transform
- "center it on impact / affected areas" (free-form)
- regenerate-full / iframe-only

---

## Example 3 — Understand a technical doc as a beginner

**Input**
- a technical document

**core.yaml (intent)**
- concepts tagged with difficulty so hard terms are visible
- a glossary's worth of term definitions captured as concept details
- low-confidence items surfaced as questions

**view.yaml (strategy)**
- role `beginner`, familiarity `beginner`
- preferred forms: `beginner_tutorial`, `glossary`, `faq`
- tone `tutorial`, density `low`, interaction_level `medium`
- emphasize: why it matters, step-by-step path

**Inside the iframe**
- a 3-step path to understanding
- a glossary of terms with short, plain explanations
- a FAQ
- an analogy for the hardest concept
- next questions to ask an AI

**Outside the iframe (prompt templates)**
- "make it even simpler" transform
- "add an analogy" (free-form)
- table transform
- regenerate-full / iframe-only

---

## Pattern across all three

Same machinery, different `view.yaml`:

| | Example 1 | Example 2 | Example 3 |
|---|---|---|---|
| reader | engineer | PdM / Biz | beginner |
| inside iframe | worktree + reading order + review checklist | purpose / impact / decisions / risks | 3 steps + glossary + FAQ |
| emphasize | dependencies, risks | impact, decisions | why-it-matters, steps |
| outside iframe | engineer + table + review-angles | biz + faq + impact | simpler + analogy + table |

The `core.yaml` (meaning) can stay largely the same; swapping `view.yaml` (strategy) is
what re-targets the explanation — which is exactly what the prompt templates let the user
do later, on their own, with another AI.
