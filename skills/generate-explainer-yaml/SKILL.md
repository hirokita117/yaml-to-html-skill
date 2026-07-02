---
name: generate-explainer-yaml
description: analyze a document, repository summary, pull request, README, design note, or specification and produce (or refine) the intermediate yaml files that drive the explainer pipeline — core.yaml (the semantic structure / meaning), view.yaml (the presentation strategy for a particular reader), and, by default, quiz.yaml (comprehension-check questions derived from core.yaml; skipped only when the user explicitly declines a quiz). use when the user wants to capture what a target means and how to show it before generating an html explainer, or wants to edit/reshape an existing core.yaml / view.yaml / quiz.yaml. the generate-explainer-html skill then turns these yaml files into a switchable, light/dark html bundle.
---

# generate-explainer-yaml

Turn an understanding target — a pasted document, repository summary, PR/diff summary,
README, design note, or spec — into the **intermediate YAML files** that the explainer
pipeline runs on:

1. `core.yaml` — the **semantic structure** of the target (meaning, not UI): concepts,
   relations, importance, difficulty, confidence, questions, risks, source refs.
2. `view.yaml` — **how to present it to this particular reader**: audience, preferred and
   avoided forms, density, tone, emphasis, generation policy.
3. `quiz.yaml` — **comprehension-check questions** derived from `core.yaml` (choices,
   answers, explanations, difficulty). Produced **by default**; skip it only when the
   user explicitly declines a quiz.

This skill is the **first half** of the pipeline. It does not produce HTML. Once the YAML
files exist, the **`generate-explainer-html`** skill reads them (by absolute path) and
builds a switchable, light/dark HTML view bundle.

```
Input (document / repo summary / PR diff / README / design doc / any technical text)
  ↓ analyze (this skill)
core.yaml   (concepts, relations, importance, difficulty, evidence, source refs)
view.yaml   (audience, preferred/avoided forms, density, emphasis)
quiz.yaml   (comprehension-check questions — default output, opt-out)
  ↓ design + generate (generate-explainer-html skill)
HTML bundle (index.html + switchable iframe views, incl. a quiz tab)
```

## What this skill does

- **Generate** `core.yaml` + `view.yaml` (+ `quiz.yaml` by default) from a fresh input.
- **Refine / reshape** an existing `core.yaml` / `view.yaml` / `quiz.yaml` (add a concept,
  fix a relation, re-target `view.yaml` at a different audience, adjust emphasis, add or
  fix quiz items, tidy the structure).

## Where to write the YAML

Write the files to a **stable directory** whose path will persist — most naturally the
bundle directory the HTML skill will build into (e.g. `./explainer-bundle/core.yaml`,
`./explainer-bundle/view.yaml`, `./explainer-bundle/quiz.yaml`), or a project folder the
user keeps. The HTML skill copies
them into the bundle and embeds their **absolute path** into the regeneration prompts, so a
local-file-reading AI can re-read them later. Do **not** use a throwaway temp path.

## Steps

1. **Read the input.** Take whatever the user pasted or pointed at. Identify the target
   type (document / repository / pull_request / design_note / spec).

2. **Author `core.yaml`.** Capture the *meaning*: concepts (with importance, difficulty,
   confidence), relations, questions, risks, and `source_refs`. Keep it compact — compress
   to what matters; do not transcribe the source. Lower `confidence` and add a `question`
   when unsure; do not invent facts. Schema: `references/core-yaml-schema.md`. Example:
   `references/sample-core.yaml`.

3. **Author `view.yaml`.** Decide how to present it to *this* reader: audience
   role/familiarity, preferred and avoided forms, density, tone, what to emphasize, and the
   `html_generation_policy`. If the user did not say, infer a sensible strategy and **state
   the assumption**. Schema: `references/view-yaml-schema.md`. Example:
   `references/sample-view.yaml`.

4. **Author `quiz.yaml` (default — skip only on explicit opt-out).** Unless the user has
   explicitly said they do not want a quiz, derive comprehension-check questions from
   `core.yaml`: concepts → single_choice / true_false; relations (`depends_on`, `calls`,
   …) → relation items; `sequence_next` chains and flows → ordering items; risks and
   questions → high-value true_false / single_choice. Spread `difficulty`, link every
   item via `related_concept_ids`, and never quiz on a low-confidence invention. Schema:
   `references/quiz-yaml-schema.md`. Example: `references/sample-quiz.yaml`.

5. **Write the files** to the stable directory and tell the user their **absolute paths**,
   so they can hand those paths to `generate-explainer-html`.

6. **(Refine mode)** When editing existing YAML, read the current file first, make the
   smallest change that satisfies the request, keep `id` values stable (relations,
   questions, and risks point at concept ids; quiz items point back at them too), and
   preserve the schema version. When refining `quiz.yaml`, keep item `id`s stable and
   **cross-check every `related_concept_ids` / `related_relation_ids` against the current
   `core.yaml`** — concept ids may have drifted since the quiz was generated.

## Hand-off to the HTML skill

After writing the YAML, the next step is the **`generate-explainer-html`** skill:

```
generate-explainer-html を使って、
  --core /abs/path/core.yaml --view /abs/path/view.yaml --quiz /abs/path/quiz.yaml
からビュー付きの HTML バンドルを作ってください。
```

(`--quiz` is omitted only when the user declined a quiz and no `quiz.yaml` was written.)

## Notes

- **core.yaml is reader-independent; view.yaml is reader-dependent.** Keeping meaning
  separate from presentation is what lets the same `core.yaml` be re-targeted at a new
  audience just by changing `view.yaml`.
- **quiz.yaml is fact-bound.** Correct answers must trace back to `core.yaml`; wrong
  choices may be invented (plausible misreadings) but each `explanation` must say why
  they are wrong. Quizzes are generated by default — omit only on explicit user opt-out.
- **Offline safety carries downstream.** The final HTML is offline and self-contained and a
  validator flags any `http://` / `https://` string. Treat any `url` in a `source_ref` as a
  *label*, not a live link — prefer `path` / `title` / `excerpt`, and drop the scheme if you
  must record a URL. See the "URLs" note in `references/core-yaml-schema.md`.

## Reference material

- `references/core-yaml-schema.md` — meaning structure schema (`core/v1`)
- `references/view-yaml-schema.md` — presentation strategy schema (`view/v1`)
- `references/quiz-yaml-schema.md` — comprehension-check quiz schema (`quiz/v1`)
- `references/sample-core.yaml` — worked `core.yaml` (a PR)
- `references/sample-view.yaml` — worked `view.yaml` (engineer reviewing the PR)
- `references/sample-quiz.yaml` — worked `quiz.yaml` (all five item types, same PR)
- `references/examples.md` — three worked intents (engineer / PdM / beginner)
- `agents/openai.yaml` — portable description of this skill for non-Claude agents
