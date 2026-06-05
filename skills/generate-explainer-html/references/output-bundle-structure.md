# Output bundle structure

The final artifact is a **self-contained bundle (a directory)** that opens in a browser
with no network access. It is not a single file — splitting views into separate files is
what makes views **additive** (you can grow the bundle one view at a time).

```
<bundle>/
  index.html          the shell (header + left prompt pane + right view switcher + ONE iframe)
  views.json          ordered manifest: {"views":[{"id","label","file"}, ...]}
  core.yaml           copied in; its absolute path is cited by the prompts
  view.yaml           copied in
  views/
    01-<id>.html       an iframe view document (full <!DOCTYPE html>, light default)
    02-<id>.html
```

`scripts/build_html.py` produces and maintains exactly this shape. It is an **assembler**:
it writes the shell and merges views into the manifest; it does not derive a fixed diagram
from `core.yaml`.

## The shell (`index.html`)

Two panes plus a header:

```text
header                    title + subtitle + light/dark THEME TOGGLE
main layout (2 panes)
  left  pane:  prompt templates ("add a view" cards, with copy buttons)
               core.yaml / view.yaml viewers (tabbed, display-only)
               help / usage
  right pane:  view switcher (tabs, one per manifest entry)
               ONE <iframe src="views/<file>#theme=...">  (the current view)
inline <style> / <script>   (no external CSS/JS)
```

- Two panes side by side on wide screens; stacks to one column on narrow screens.
- **Light theme by default**, with a header toggle that flips `data-theme="dark"` on the
  shell. No storage (forbidden), so the theme resets to light on reload.
- Respects `prefers-reduced-motion`; keyboard operable; visible focus styles.

## The view switcher + iframe (right pane)

- One `<iframe id="view-frame" sandbox="allow-scripts" src="views/<file>#theme=...">`.
- A tab per view (from `views.json`). Clicking a tab sets `iframe.src` to that view file.
- The shell propagates its theme into the cross-origin iframe via the **URL hash**
  (`#theme=dark|light`); each view reads its own `location.hash` (load + `hashchange`).
- `sandbox="allow-scripts"` (never `allow-same-origin`): the view runs in a unique origin
  and cannot reach the parent DOM, storage, or cookies.

## Each view document (`views/NN-<id>.html`)

- A **full HTML document** tailored to the target and the reader, loaded via local `src`.
- The representation is **not fixed** — table, worktree, cards, faq, comparison, sequence,
  reading path, risk map, dependency map, glossary, tutorial, review checklist, …
- Must include: source references, important concepts, relations, what to read next, next
  questions. Must have visual structure, not flat prose.
- **Light by default**; reads `#theme` to support dark. See `html-generation-rules.md`.

## The prompt templates (left pane)

- Not a chat UI. A set of cards that ask a local-file-reading AI to author **one new view**.
- Each card: title, usage description, prompt body (collapsible), copy button, optional tags.
- Prompts cite the YAML by **absolute path** (`{{core_yaml_path}}` / `{{view_yaml_path}}`)
  and never embed YAML content.
- See `prompt-template-patterns.md` for the required set and `sample-prompts.json`.

## YAML viewers (left pane)

- `core.yaml` and `view.yaml` are embedded as read-only text, toggled by tabs (display-only).
- They make the bundle self-explanatory. (The prompts do **not** use this embedded copy;
  they point at the on-disk file by absolute path.)

## The manifest (`views.json`)

- The single source of truth for the view list and order. Tabs and view filenames both
  derive from it. Re-running the build **appends** new views and preserves existing ones.

## Safety properties of the output

- No network requests, no external scripts/CSS, no remote iframes, no storage, no cookies.
- The iframe cannot reach the parent page (no `allow-same-origin`); a local relative `src`
  is allowed, a remote `src` is not.
- Verified by `scripts/validate_html.py` over `index.html` and every `views/*.html`.
