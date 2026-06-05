# core.yaml — semantic structure of the understanding target

`core.yaml` captures **what the target means**, not how it should look. It is the
single semantic source of truth that every later step (view strategy, HTML generation,
prompt templates) builds on. It is deliberately UI-agnostic: the same `core.yaml` can be
rendered as a table, a worktree, a FAQ, a sequence, or anything else.

## Mental model

```
Input (doc / repo / PR / design note / spec)
   ↓ analyze
core.yaml  ← concepts, relations, importance, difficulty, evidence, source references
```

Think of `core.yaml` as a **map of meaning**:

- *concepts* — the things worth understanding (files, modules, ideas, decisions, risks…)
- *relations* — how those things connect (depends_on, calls, changes, contrasts…)
- *importance / difficulty / confidence* — where attention and caution should go
- *source_refs* — the evidence, so every claim can be traced back

## Do / Don't

- ✅ Describe meaning, structure, importance, difficulty, and evidence.
- ✅ Keep it small: compress to what matters; do not transcribe the whole source.
- ❌ Do not encode layout, colors, components, or "render this as a table".
- ❌ Do not paste large verbatim excerpts of the original text (short excerpts only).
- ❌ Do not invent facts; lower `confidence` and add a `question` when unsure.

## Schema (`version: core/v1`)

```yaml
version: core/v1

target:
  type: document | repository | pull_request | design_note | spec | other
  title: string            # short human title
  summary: string          # 1–3 sentences: what this target is
  source_label: string     # where it came from (e.g. "PR #482", "README")

concepts:
  - id: string             # stable id, referenced by relations/questions/risks
    label: string          # short display name
    kind: file | module | function | concept | flow | decision | risk | actor | requirement | unknown
    summary: string        # one line
    detail: string         # optional deeper explanation
    importance: low | medium | high
    difficulty: low | medium | high
    confidence: number      # 0.0–1.0, how sure you are
    source_refs:            # evidence for THIS concept (optional)
      - id: string
        path: string        # file path or logical location
        url: string         # OPTIONAL. Prefer omitting; see "URLs" note below.
        excerpt: string     # SHORT quote, not the whole thing
        lines:
          start: number
          end: number

relations:
  - id: string
    from: string            # concept id
    to: string              # concept id
    type: depends_on | calls | contains | changes | affects | explains | contrasts | sequence_next | blocks | supports | unknown
    label: string           # short edge label
    reason: string          # why this relation exists
    confidence: number

questions:                  # what a reader should still ask
  - id: string
    question: string
    why_it_matters: string
    related_concept_ids:
      - string

risks:                      # what could go wrong / needs care
  - id: string
    label: string
    description: string
    severity: low | medium | high
    related_concept_ids:
      - string

source_refs:                # top-level evidence registry (optional, deduped)
  - id: string
    title: string
    type: file | diff | document | url | note
    path: string
    url: string             # OPTIONAL — see note
    excerpt: string
```

## Field notes

- **id** values are the glue. Keep them stable and unique; relations, questions, and
  risks point at concept ids.
- **importance vs difficulty** are different axes. Importance = "how much it matters to
  understand"; difficulty = "how hard it is to understand". Both drive the visual
  emphasis the generated UI should give.
- **confidence** is your honesty signal. Low confidence should surface as a visible
  marker in the UI and often as a `question`.
- **source_refs** make the output trustworthy. Every important concept should be
  traceable to a `path` (and optionally `lines`).

## A note on URLs (offline safety)

The final HTML is **offline and self-contained**, and `validate_html.py` flags any
`http://` / `https://` string as a potential external dependency. So:

- Prefer `path`, `title`, and `excerpt` to identify a source.
- Treat any `url` as a **label**, not a live link. If you must record a URL, keep it out
  of the generated HTML (or write it as plain text without the `http`/`https` scheme,
  e.g. `example.com/path`), so the output stays validatable and offline.

## Minimal example

```yaml
version: core/v1
target:
  type: pull_request
  title: "Add rate limiting to the public API"
  summary: "Token-bucket rate limiter as middleware on the public API."
  source_label: "PR #482"
concepts:
  - id: c_middleware
    label: "RateLimitMiddleware"
    kind: module
    summary: "Rejects requests over the limit."
    importance: high
    difficulty: medium
    confidence: 0.9
    source_refs:
      - id: r_mw
        path: "src/api/middleware/rate_limit.py"
        lines: { start: 14, end: 76 }
relations:
  - id: rel1
    from: c_middleware
    to: c_store
    type: depends_on
    label: "asks for a token"
    confidence: 0.95
```

See `sample-core.yaml` for a fuller, working example.
