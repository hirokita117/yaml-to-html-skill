# view.yaml — presentation strategy for one reader

`view.yaml` answers a different question from `core.yaml`:

- `core.yaml` = **what the target means** (reader-independent)
- `view.yaml` = **how to show it so THIS reader understands fastest** (reader-dependent)

It is **not** a command to a fixed renderer. It is a *middle representation* that tells
the HTML-generating AI which forms to prefer, which to avoid, how dense to be, and what
to emphasize. The same `core.yaml` plus a different `view.yaml` should produce a
meaningfully different HTML.

## Why a separate file

Understanding is personal. One reader thinks in tables; another in worktrees, cards,
FAQs, comparisons, sequences, stories, reading orders, or impact maps. Splitting
"meaning" from "presentation" lets the user re-target the *same* meaning at a new
audience just by changing `view.yaml` — which is exactly what the iframe-only and
"regenerate" prompt templates do.

## Schema (`version: view/v1`)

```yaml
version: view/v1

audience:
  role: engineer | designer | product_manager | business | beginner | custom
  familiarity: beginner | intermediate | advanced | unknown
  stated_preferences:        # forms the user said they like
    - worktree
    - sequence
  dislikes:                  # forms to avoid for this reader
    - dense_table

intent:
  primary_goal: string       # the one thing this reader wants
  secondary_goals:
    - string

presentation:
  preferred_forms:           # bias the iframe UI toward these
    - worktree
    - cards
    - faq
  avoid_forms:
    - dense_table
  density: low | medium | high
  tone: concise | friendly | technical | tutorial
  visual_style: string       # free text, e.g. "clean, readable, not decorative"
  interaction_level: low | medium | high   # how much expand/filter/tab to add

focus:
  emphasize:                 # which axes to foreground
    - purpose
    - impact
    - dependencies
    - risks
    - reading_order
  de_emphasize:
    - minor_details

html_generation_policy:
  allow_creative_layout: true
  must_include:              # the UI MUST contain these
    - overview
    - source_references
    - prompt_templates
  should_include:            # nice-to-have
    - progressive_disclosure
    - visual_grouping
    - next_questions
  must_not_include:          # hard safety / scope limits
    - external_script
    - remote_css
    - network_request
```

## Vocabulary for `preferred_forms` / `avoid_forms`

These are *suggestions* to the generator, not an enum it must close over. Common values:

`table`, `worktree`, `cards`, `faq`, `comparison`, `sequence`, `timeline`,
`reading_path`, `risk_map`, `dependency_map`, `glossary`, `beginner_tutorial`,
`review_checklist`, `decision_map`, `impact_map`, `story`.

The generator may combine several (e.g. *worktree + reading_path + review_checklist*).

## Field notes

- **stated_preferences / dislikes** are the strongest signal — honor them. If the reader
  dislikes `dense_table`, do not make a wall-of-table the primary view.
- **density** controls how much progressive disclosure to use. `high` density readers
  want everything visible; `low` density readers want a small overview that expands.
- **interaction_level** decides how much client-side interaction (tabs, filters,
  collapsible trees) to add — all of it inside the iframe, none of it networked.
- **focus.emphasize** maps to the `core.yaml` axes (importance, difficulty, risk,
  relations, reading order) that should be visually loud.
- **html_generation_policy.must_not_include** is a safety contract. It always forbids
  external scripts, remote CSS, and network requests — see `html-generation-rules.md`.

## How `view.yaml` is inferred when the user says little

If the user gives no explicit preferences, infer a reasonable `view.yaml` from context
and **state the assumption** in the output. For example:

- "review this PR" → role `engineer`, forms `worktree + reading_path + review_checklist`.
- "explain this spec to leadership" → role `business`, forms `impact_map + faq`.
- "I'm new to this" → role `beginner`, forms `beginner_tutorial + glossary + faq`.

Then leave the user a prompt template to re-target if the guess was wrong.

See `sample-view.yaml` for a working example (engineer reviewing a PR).
