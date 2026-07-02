# quiz.yaml — comprehension-check questions derived from core.yaml

`quiz.yaml` captures **retrieval-practice questions** that help a reader confirm (and
deepen) their understanding of the target. It is derived from `core.yaml` — every correct
answer must be traceable to a fact recorded there — and rendered by the HTML skill as an
interactive quiz view (answer → instant grading → explanation).

By default the pipeline produces `quiz.yaml` alongside `core.yaml` / `view.yaml`; it is
skipped only when the user explicitly declines a quiz.

## Mental model

```
core.yaml  (facts: concepts, relations, risks, questions)
   ↓ derive
quiz.yaml  ← questions + choices + answers + explanations, linked back to concept ids
   ↓ render (generate-explainer-html skill)
quiz view  (interactive tab: answer → grade → explain)
```

Think of `quiz.yaml` as a **question bank over the map of meaning**:

- *items* — one question each, typed (choice / true-false / relation / ordering)
- *answer + explanation* — instant feedback material, pre-authored, never fetched
- *difficulty / audience_hint* — how a view decides what to ask first, and to whom
- *related_concept_ids* — the link back into `core.yaml`, so a wrong answer can point
  the reader at the concept to re-read

## Do / Don't

- ✅ Derive correct answers **only from facts in `core.yaml`** (concept summaries/details,
  relation reasons, risks, questions).
- ✅ Invent *plausible* wrong choices (common misreadings), and let `explanation` say why
  they are wrong.
- ✅ Spread `difficulty` across items and link every item via `related_concept_ids`.
- ❌ Do not quiz on inventions: if the underlying fact has low `confidence` in
  `core.yaml`, skip the item or carry that low `confidence` visibly.
- ❌ Do not encode presentation (colors, layout, "show as cards") — that is the view's job.
- ❌ Do not put live URLs anywhere (see "URLs" note below).

## Schema (`version: quiz/v1`)

```yaml
version: quiz/v1

target:
  title: string             # same target as core.yaml
  source_label: string      # e.g. "PR #482" — a label, never a live URL
  core_ref: string          # optional: path/label of the core.yaml this derives from

meta:                       # optional
  notes: string             # generation assumptions (e.g. how distractors were made)

items:
  - id: string              # stable id; refine mode keeps it
    type: single_choice | multiple_choice | true_false | relation | ordering
    question: string
    difficulty: low | medium | high
    choices:                # REQUIRED for every type (true_false too — see notes)
      - id: string          # e.g. ch_a
        text: string
    answer:                 # exactly ONE of the two keys, by type
      correct_choice_ids:   # single_choice: 1 id / multiple_choice: n ids /
        - string            # true_false: the id of the correct ○ or × choice /
                            # relation: 1 id
      correct_order:        # ordering ONLY: choice ids in the correct sequence
        - string
    explanation: string     # shown after grading; also says why wrong choices are wrong
    related_concept_ids:    # recommended: concept ids in core.yaml
      - string
    related_relation_ids:   # optional: relation ids (for relation/ordering items)
      - string
    audience_hint:          # optional soft targeting; views may filter/order by it
      recommended_roles:
        - beginner | engineer | designer | product_manager | business | custom
    confidence: number      # optional, 0.0–1.0 — same honesty signal as core/v1
    source_refs:            # optional evidence, same shape as core/v1
      - id: string
        path: string
        excerpt: string
        lines:
          start: number
          end: number
```

## Field notes

- **One grading model for every type.** `true_false` still declares two explicit
  `choices` (○ / ×) and answers through `answer.correct_choice_ids`, so a view can grade
  all five types with the same logic: `multiple_choice` = exact set match, `ordering` =
  exact sequence match (`answer.correct_order` lists choice ids in correct order),
  everything else = the one correct choice id.
- **`relation` items** are structurally single-choice ("A と B の関係は？" with
  relation-type descriptions as choices) but keep their own `type` so views can group
  them; derive them from `core.yaml relations[]` and record `related_relation_ids`.
- **`ordering` items** come from `sequence_next` chains, flow-kind concepts, or a
  reading order. Present the steps as `choices` and put the correct sequence in
  `answer.correct_order`.
- **Derivation map** (where items come from):
  - concepts → `single_choice` / `true_false` ("Xの役割は？" "Xは〜である ○か×か")
  - relations (`depends_on`, `calls`, …) → `relation`
  - `sequence_next` chains / flows → `ordering`
  - risks / questions → high-value `true_false` / `single_choice` (misconception busters)
- **difficulty + audience_hint drive adaptation.** Views order/select items by the
  reader (`view.yaml audience`) and per-item `difficulty` — e.g. beginners start with
  easy `true_false`, engineers lead with `relation` / `ordering`.
- **No persistence downstream.** The rendered quiz keeps score only in page state; a
  reload resets it (browser storage is forbidden in the generated HTML). Author
  explanations so each item is self-contained.

## A note on URLs (offline safety)

Same rule as `core.yaml`: the final HTML is offline and self-contained, and
`validate_html.py` flags any `http://` / `https://` string. Identify sources by `path`
and `excerpt`; if you must record a URL, drop the scheme (e.g. `example.com/path`).

## Minimal example

```yaml
version: quiz/v1
target:
  title: "Add rate limiting to the public API"
  source_label: "PR #482"
  core_ref: "core.yaml"
items:
  - id: q_mw_role
    type: single_choice
    question: "RateLimitMiddleware の役割はどれ？"
    difficulty: low
    choices:
      - id: ch_a
        text: "上限を超えたリクエストを 429 で拒否する"
      - id: ch_b
        text: "リクエストをログに記録する"
    answer:
      correct_choice_ids: [ch_a]
    explanation: "ミドルウェアはストアにトークンを問い合わせ、空なら 429 を返す。ログ記録は役割ではない。"
    related_concept_ids: [c_middleware]
```

See `sample-quiz.yaml` for a fuller, working example covering all five item types.
