# CLAUDE.md

Guidance for Claude Code (and maintainers) when working in this repository.

## Repo orientation

This is a Claude Code plugin with two skills. See [README.md](README.md) for the full
picture and [CONTRIBUTING.md](CONTRIBUTING.md) for the contributor workflow.

- `skills/generate-explainer-yaml/` — produces `core.yaml` + `view.yaml` (no scripts).
- `skills/generate-explainer-html/scripts/` — `build_html.py` (assembles/grows the bundle)
  and `validate_html.py` (offline-safety linter).
- `.claude-plugin/plugin.json` + `.claude-plugin/marketplace.json` — the manifests; both
  carry the plugin `version`.

## Commands

Build and validate the sample bundle (run from `skills/generate-explainer-html/`):

```bash
python3 scripts/build_html.py \
  --bundle ./sample-bundle \
  --core ../generate-explainer-yaml/references/sample-core.yaml \
  --view ../generate-explainer-yaml/references/sample-view.yaml \
  --prompts references/sample-prompts.json \
  --view-html "エンジニア=references/sample-iframe.html"

python3 scripts/validate_html.py ./sample-bundle/index.html ./sample-bundle/views/*.html --strict
```

## Conventions

- **Python 3.9+, standard library only.** No external dependencies — don't add any. Use
  `python3`.
- **Generated HTML must stay offline/self-contained.** Always run `validate_html.py`
  (`--strict`) on anything that changes the bundle; it must exit `0`.
- **Branches:** `feat/` `fix/` `chore/` `docs/` prefixes; PR into `main`.
- **No version field outside the two manifests.** SKILL.md frontmatter and the
  `agents/openai.yaml` `version:` are unrelated to the plugin version — leave them alone
  when releasing.

## Release process

Releases are **manual** — there is no CI and no `.github/workflows/`. Do **not** add release
automation unless explicitly asked. Change history is kept in **GitHub Releases only** (no
`CHANGELOG.md`).

Steps to publish version `X.Y.Z`:

1. **Use SemVer**, with git tags in the form `vX.Y.Z`.
2. **Bump the version in BOTH manifests in the same change** — they must always match:
   - `.claude-plugin/plugin.json` → `"version"`
   - `.claude-plugin/marketplace.json` → the plugin entry's `"version"`

   ⚠️ Bumping only one of these ships a broken/inconsistent release. Never bump one alone.
3. Land the change on `main` via a PR.
4. Tag the merge commit and push the tag:

   ```bash
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```

5. **Create a GitHub Release** for the tag — the release notes are the only changelog:

   ```bash
   gh release create vX.Y.Z --title "vX.Y.Z" --notes "<summary of changes>"
   ```

6. Users update via the flow already documented in the README
   ([Updating the plugin](README.md#updating-the-plugin)):
   `/plugin marketplace update yaml-to-html-skill` → `/plugin install yaml-to-html@yaml-to-html-skill`
   → `/reload-plugins`. Keep tags/Releases consistent with the manifest version so this
   flow resolves correctly.
