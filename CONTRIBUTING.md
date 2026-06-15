# Contributing

Thanks for your interest in improving **yaml-to-html explainer** — a Claude Code plugin
with two skills (`generate-explainer-yaml`, `generate-explainer-html`). This guide covers
how to set up, test, and submit changes. For what the project does, see the
[README](README.md).

## Project overview

- `skills/generate-explainer-yaml/` — produces `core.yaml` (meaning) + `view.yaml`
  (presentation strategy). Pure LLM reasoning, no scripts.
- `skills/generate-explainer-html/` — turns that YAML into a self-contained HTML bundle,
  via `scripts/build_html.py` (assembler) and `scripts/validate_html.py` (safety linter).
- `.claude-plugin/` — `plugin.json` + `marketplace.json` (the plugin/marketplace manifests).

## Dev setup

- **Python 3.9+** (the scripts use `from __future__ import annotations` and `list[str]`
  type hints). Use `python3` if `python` is not on your PATH.
- **No dependencies** — both scripts are standard-library only. No virtualenv or install
  step is required.

## Running and testing the sample

Any change that affects the generated bundle must pass the safety validator. Build the
bundled sample and validate it **before opening a PR**:

```bash
cd skills/generate-explainer-html

python3 scripts/build_html.py \
  --bundle ./sample-bundle \
  --core ../generate-explainer-yaml/references/sample-core.yaml \
  --view ../generate-explainer-yaml/references/sample-view.yaml \
  --prompts references/sample-prompts.json \
  --view-html "エンジニア=references/sample-iframe.html"

python3 scripts/validate_html.py ./sample-bundle/index.html ./sample-bundle/views/*.html --strict
```

`validate_html.py` must exit `0`. With `--strict` it also fails on warnings. The
`sample-bundle/` directory is git-ignored, so it will not be committed — delete it when
you're done. To open the result, see
[Opening the bundle](README.md#opening-the-bundle-browser-note) (use Firefox over `file://`,
or serve the folder).

`validate_html.py` rejects anything that breaks the offline/self-contained promise:
external scripts/stylesheets/iframes, `fetch`/`XMLHttpRequest`/`WebSocket`,
storage/cookies, parent-frame access, and any `http(s)://` URL. Keep generated views
offline and sandboxed.

## Branch & PR conventions

- Branch from `main` using a type prefix: `feat/<desc>`, `fix/<desc>`, `chore/<desc>`,
  `docs/<desc>`.
- Keep PRs small and focused. Open a PR against `main`.

**PR checklist:**

- [ ] If the change affects generated HTML, `validate_html.py --strict` passes on the sample.
- [ ] If the change bumps the plugin version, **both** `.claude-plugin/plugin.json` and
      `.claude-plugin/marketplace.json` are updated to the same version (see Releasing).
- [ ] README / skill docs updated if behavior or commands changed.

## Releasing

Releases are cut manually (no CI). The plugin version lives in **two files that must stay
in sync**, and release notes live in **GitHub Releases**. The authoritative step-by-step
procedure is in [`CLAUDE.md`](CLAUDE.md#release-process) — follow it when publishing a new
version.

## License

By contributing, you agree that your contributions are licensed under the
[MIT License](LICENSE).
