#!/usr/bin/env python3
"""build_html.py

Build (and incrementally grow) a multi-file *bundle* for the
``generate-explainer-html`` skill.

This script is an *assembler*, not a renderer. It does NOT look at the meaning of
``core.yaml`` and turn it into a fixed diagram. Each explanation UI is an iframe HTML
document authored by an AI; this script only manages the outer shell and the bundle.

What it produces
----------------
A bundle is a *directory* (not a single file):

    <bundle>/
      index.html            the shell: header (theme toggle) + left prompt pane
                            + right pane with a VIEW-SWITCHER and ONE <iframe>
      views.json            ordered manifest: {"views": [{"id","label","file"}, ...]}
      core.yaml             copied from --core (its absolute path is cited by prompts)
      view.yaml             copied from --view
      quiz.yaml             copied from --quiz (optional; comprehension-check questions)
      views/
        01-<id>.html        an AI-authored iframe document (full <!DOCTYPE html>)
        02-<id>.html

The right-pane iframe loads each view via ``src="views/<file>"`` (NOT srcdoc) and a tab
switcher swaps which view file it shows. The iframe stays ``sandbox="allow-scripts"``
(never ``allow-same-origin``).

Additive views
--------------
Each run MERGES the ``--view-html`` entries into ``views.json`` and regenerates
``index.html`` from the full manifest. Re-running with one new ``--view-html`` APPENDS a
view and preserves the existing ones — that is how "add a table view next to the beginner
view" works. Re-running an existing view (same slugified id) updates it in place.

Placeholder substitution (paths, not content)
----------------------------------------------
Prompt strings inside ``prompts.json`` may contain ``{{core_yaml_path}}``,
``{{view_yaml_path}}``, and ``{{quiz_yaml_path}}``. Those tokens are replaced with the
*absolute path* of the copied-in ``core.yaml`` / ``view.yaml`` / ``quiz.yaml`` so a
local-file-reading AI can open them. The YAML *content* is never embedded into a prompt.
Any other ``{{...}}`` token (for example ``{{希望する表現}}``) is left untouched for the
user to fill in.

Example
-------
    python scripts/build_html.py \
      --bundle ./explainer-bundle \
      --core core.yaml \
      --view view.yaml \
      --quiz quiz.yaml \
      --prompts prompts.json \
      --view-html "エンジニア=engineer.html" \
      --view-html "クイズ=quiz.html"
"""

from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------

def read_text(path: str) -> str:
    """Read a UTF-8 text file, raising a friendly error if it is missing."""
    p = Path(path)
    if not p.is_file():
        raise SystemExit(f"build_html.py: input file not found: {path}")
    return p.read_text(encoding="utf-8")


def esc(text: str) -> str:
    """HTML-escape text for safe display inside an element (quotes included).

    Display uses ``<pre>``; reading ``element.textContent`` in the browser recovers
    the original characters, so copy buttons still yield the exact source text.
    """
    return html.escape(text, quote=True)


def fill_placeholders(text: str, mapping: dict[str, str]) -> str:
    """Replace known ``{{key}}`` tokens; leave every other token untouched."""
    for key, value in mapping.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def slugify(label: str) -> str:
    """Derive a filesystem/URL-friendly id from a tab label.

    Keeps Unicode alphanumerics (so Japanese labels stay meaningful) plus ``-``/``_``;
    every other character (whitespace, punctuation, ``#``, ``/`` …) becomes ``-``.
    Collapses repeats, trims, and falls back to ``view`` when empty.
    """
    out = []
    for ch in label.strip().lower():
        if ch.isalnum() or ch in "-_":
            out.append(ch)
        else:
            out.append("-")
    s = "".join(out)
    while "--" in s:
        s = s.replace("--", "-")
    return s.strip("-_") or "view"


def load_prompts(path: str) -> list[dict]:
    raw = read_text(path)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:  # pragma: no cover - user input error
        raise SystemExit(f"build_html.py: could not parse prompts JSON ({path}): {exc}")
    if not isinstance(data, list):
        raise SystemExit("build_html.py: prompts file must contain a JSON array")
    return data


def load_manifest(bundle: Path) -> list[dict]:
    """Read ``views.json`` if present; return its ordered view list (else [])."""
    path = bundle / "views.json"
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"build_html.py: could not parse {path}: {exc}")
    views = data.get("views") if isinstance(data, dict) else None
    if not isinstance(views, list):
        return []
    cleaned: list[dict] = []
    for entry in views:
        if isinstance(entry, dict) and entry.get("id") and entry.get("label"):
            cleaned.append({"id": str(entry["id"]), "label": str(entry["label"]),
                            "file": str(entry.get("file", ""))})
    return cleaned


def write_manifest(bundle: Path, views: list[dict]) -> None:
    payload = {"views": [{"id": v["id"], "label": v["label"], "file": v["file"]} for v in views]}
    (bundle / "views.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_view_specs(specs: list[str]) -> list[tuple[str, str]]:
    """Parse repeatable ``--view-html "LABEL=PATH"`` values into (label, path) pairs."""
    pairs: list[tuple[str, str]] = []
    for spec in specs:
        if "=" not in spec:
            raise SystemExit(f'build_html.py: --view-html must be "LABEL=PATH": {spec!r}')
        label, path = spec.split("=", 1)
        label, path = label.strip(), path.strip()
        if not label or not path:
            raise SystemExit(f'build_html.py: --view-html must be "LABEL=PATH": {spec!r}')
        pairs.append((label, path))
    return pairs


# ---------------------------------------------------------------------------
# rendering fragments
# ---------------------------------------------------------------------------

def render_cards(prompts: list[dict], mapping: dict[str, str]) -> str:
    cards: list[str] = []
    for index, item in enumerate(prompts):
        if not isinstance(item, dict):
            raise SystemExit("build_html.py: each prompt entry must be a JSON object")
        pid = str(item.get("id", f"prompt-{index}"))
        dom_id = "prompt-" + "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in pid)
        title = str(item.get("title", pid))
        description = str(item.get("description", ""))
        body = fill_placeholders(str(item.get("prompt", "")), mapping)
        tags = item.get("tags") or []
        tags_html = ""
        if isinstance(tags, list) and tags:
            chips = "".join(f'<span class="tag">{esc(str(t))}</span>' for t in tags)
            tags_html = f'<div class="tags">{chips}</div>'

        cards.append(
            "\n".join(
                [
                    '<article class="card">',
                    '  <header class="card-head">',
                    f"    <h3 class=\"card-title\">{esc(title)}</h3>",
                    f"    {tags_html}",
                    "  </header>",
                    f'  <p class="card-desc">{esc(description)}</p>',
                    '  <details class="prompt-details">',
                    "    <summary>プロンプト本文を表示 / 折りたたみ</summary>",
                    f'    <pre class="prompt-body" id="{dom_id}">{esc(body)}</pre>',
                    "  </details>",
                    f'  <button class="copy-btn" type="button" data-target="{dom_id}">'
                    "プロンプトをコピー</button>",
                    "</article>",
                ]
            )
        )
    if not cards:
        cards.append('<p class="empty">プロンプトテンプレートがありません。</p>')
    return "\n".join(cards)


def render_meta(core_text: str | None, view_text: str | None,
                quiz_text: str | None = None) -> tuple[str, str]:
    """Return (tab_buttons_html, panels_html) for the YAML viewer panels (display-only)."""
    tabs: list[str] = []
    panels: list[str] = []
    if core_text is not None:
        tabs.append(
            '<button class="tab-btn" type="button" role="tab" aria-selected="false" '
            'data-panel="panel-core">core.yaml</button>'
        )
        panels.append(
            '<div class="panel hidden" id="panel-core" role="tabpanel">'
            '<p class="panel-note">理解対象の意味構造（UI ではなく意味）。表示専用です。</p>'
            f'<pre class="yaml-body">{esc(core_text)}</pre></div>'
        )
    if view_text is not None:
        tabs.append(
            '<button class="tab-btn" type="button" role="tab" aria-selected="false" '
            'data-panel="panel-view">view.yaml</button>'
        )
        panels.append(
            '<div class="panel hidden" id="panel-view" role="tabpanel">'
            '<p class="panel-note">この人にどう見せると分かりやすいかの方針。表示専用です。</p>'
            f'<pre class="yaml-body">{esc(view_text)}</pre></div>'
        )
    if quiz_text is not None:
        tabs.append(
            '<button class="tab-btn" type="button" role="tab" aria-selected="false" '
            'data-panel="panel-quiz">quiz.yaml</button>'
        )
        panels.append(
            '<div class="panel hidden" id="panel-quiz" role="tabpanel">'
            '<p class="panel-note">理解度チェック用のクイズ定義。表示専用です。</p>'
            f'<pre class="yaml-body">{esc(quiz_text)}</pre></div>'
        )
    return "\n".join(tabs), "\n".join(panels)


def render_view_tabs(views: list[dict]) -> str:
    """Return the right-pane view-switcher tab buttons (first one active)."""
    tabs: list[str] = []
    for i, v in enumerate(views):
        active = " active" if i == 0 else ""
        selected = "true" if i == 0 else "false"
        tabs.append(
            f'<button class="view-tab{active}" type="button" role="tab" '
            f'aria-selected="{selected}" data-file="{esc("views/" + v["file"])}">'
            f'{esc(v["label"])}</button>'
        )
    return "\n        ".join(tabs)


# ---------------------------------------------------------------------------
# the outer shell (inline CSS + inline JS, no external dependency)
# ---------------------------------------------------------------------------

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__ — adaptive understanding</title>
<style>
:root{
  --bg:#f7f8fa; --panel:#ffffff; --panel-2:#f1f3f7; --border:#e3e6ec;
  --text:#1d2330; --muted:#5b6577; --accent:#2b6cff; --accent-2:#1a9e6b;
  --chip:#eef1f6; --code-bg:#f4f6fa; --danger:#d6453c; --radius:12px;
}
:root[data-theme="dark"]{
  --bg:#0f1115; --panel:#171a21; --panel-2:#1f232c; --border:#2c313c;
  --text:#e6e9ef; --muted:#9aa3b2; --accent:#5aa9ff; --accent-2:#36c08f;
  --chip:#262b36; --code-bg:#0c0e13; --danger:#ff6b6b;
}
*{box-sizing:border-box}
html,body{margin:0;padding:0}
body{
  background:var(--bg); color:var(--text);
  font-family:system-ui,-apple-system,"Segoe UI",Roboto,"Hiragino Kaku Gothic ProN",
    "Noto Sans JP",Meiryo,sans-serif;
  line-height:1.6; -webkit-font-smoothing:antialiased;
}
.app{display:flex;flex-direction:column;min-height:100vh}
.app-header{
  padding:14px 20px;border-bottom:1px solid var(--border);
  background:linear-gradient(180deg,var(--panel),var(--panel-2));
  position:sticky;top:0;z-index:5;
}
.header-row{display:flex;align-items:flex-start;justify-content:space-between;gap:12px}
.app-header h1{margin:0;font-size:18px;letter-spacing:.2px}
.app-header .subtitle{margin:4px 0 0;color:var(--muted);font-size:13px}
.app-header .source-label{color:var(--accent-2)}
.theme-toggle{
  flex:none;background:var(--chip);color:var(--text);border:1px solid var(--border);
  border-radius:999px;padding:6px 12px;font-size:12px;cursor:pointer;white-space:nowrap;
}
.theme-toggle:hover{border-color:var(--accent)}
.theme-toggle:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.layout{display:grid;grid-template-columns:minmax(320px,440px) 1fr;gap:0;flex:1;min-height:0}
.pane{min-width:0;min-height:0}
.pane-left{
  border-right:1px solid var(--border);background:var(--panel);
  display:flex;flex-direction:column;max-height:calc(100vh - 60px);overflow:hidden;
}
.tabs{display:flex;gap:6px;padding:12px 12px 0;flex-wrap:wrap}
.tab-btn{
  background:var(--chip);color:var(--muted);border:1px solid var(--border);
  border-radius:999px;padding:6px 12px;font-size:12px;cursor:pointer;
}
.tab-btn:hover{color:var(--text)}
.tab-btn.active{background:var(--accent);color:#fff;border-color:var(--accent);font-weight:600}
.tab-btn:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.left-scroll{overflow-y:auto;padding:12px;flex:1}
.panel.hidden{display:none}
.panel-note{color:var(--muted);font-size:12px;margin:0 0 8px}
.intro{font-size:13px;color:var(--muted);margin:0 0 12px}
.card{
  background:var(--panel-2);border:1px solid var(--border);border-radius:var(--radius);
  padding:14px;margin:0 0 12px;
}
.card-head{display:flex;align-items:flex-start;justify-content:space-between;gap:8px}
.card-title{margin:0;font-size:14px}
.card-desc{margin:6px 0 10px;color:var(--muted);font-size:13px}
.tags{display:flex;gap:4px;flex-wrap:wrap}
.tag{
  background:var(--chip);color:var(--accent);border:1px solid var(--border);
  border-radius:6px;padding:1px 7px;font-size:11px;white-space:nowrap;
}
.prompt-details{margin:0 0 10px}
.prompt-details summary{cursor:pointer;color:var(--accent);font-size:12px;user-select:none}
.prompt-details summary:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.prompt-body,.yaml-body{
  background:var(--code-bg);border:1px solid var(--border);border-radius:8px;
  padding:10px;margin:8px 0 0;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
  font-size:12px;white-space:pre-wrap;word-break:break-word;max-height:340px;overflow:auto;
}
.copy-btn{
  background:var(--accent);color:#fff;border:0;border-radius:8px;
  padding:8px 14px;font-size:13px;font-weight:600;cursor:pointer;
}
.copy-btn:hover{filter:brightness(1.06)}
.copy-btn:focus-visible{outline:2px solid var(--text);outline-offset:2px}
.copy-btn.copied{background:var(--accent-2)}
.help h2{font-size:14px;margin:14px 0 6px}
.help ul{margin:0 0 10px;padding-left:20px}
.help li{font-size:13px;color:var(--muted);margin:2px 0}
.help code{background:var(--chip);padding:1px 5px;border-radius:4px;font-size:12px}
.pane-right{display:flex;flex-direction:column;background:var(--bg);min-height:360px}
.preview-bar{
  padding:8px 12px;border-bottom:1px solid var(--border);color:var(--muted);font-size:12px;
  display:flex;align-items:center;gap:10px;flex-wrap:wrap;
}
.preview-bar .dot{width:8px;height:8px;border-radius:50%;background:var(--accent-2);flex:none}
.view-switcher{display:flex;gap:6px;flex-wrap:wrap}
.view-tab{
  background:var(--chip);color:var(--muted);border:1px solid var(--border);
  border-radius:999px;padding:5px 12px;font-size:12px;cursor:pointer;
}
.view-tab:hover{color:var(--text)}
.view-tab.active{background:var(--accent);color:#fff;border-color:var(--accent);font-weight:600}
.view-tab:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.preview-wrap{flex:1;min-height:0;padding:14px}
.preview{
  width:100%;height:100%;min-height:520px;border:1px solid var(--border);
  border-radius:var(--radius);background:var(--panel);
}
.empty{color:var(--muted);font-size:13px}
@media (max-width:860px){
  .layout{grid-template-columns:1fr}
  .pane-left{max-height:none;border-right:0;border-bottom:1px solid var(--border)}
  .preview{min-height:480px}
}
@media (prefers-reduced-motion:reduce){
  *{transition:none !important;animation:none !important;scroll-behavior:auto !important}
}
</style>
</head>
<body>
<div class="app">
  <header class="app-header">
    <div class="header-row">
      <div>
        <h1>__TITLE__</h1>
        <p class="subtitle">__SUBTITLE__</p>
      </div>
      <button class="theme-toggle" type="button" id="theme-toggle" aria-label="テーマ切り替え">🌙 ダーク</button>
    </div>
  </header>
  <main class="layout">
    <section class="pane pane-left" aria-label="プロンプトテンプレートとメタデータ">
      <div class="tabs" role="tablist">
        <button class="tab-btn active" type="button" role="tab" aria-selected="true" data-panel="panel-prompts">テンプレート</button>
        __META_TABS__
        <button class="tab-btn" type="button" role="tab" aria-selected="false" data-panel="panel-help">使い方</button>
      </div>
      <div class="left-scroll">
        <div class="panel" id="panel-prompts" role="tabpanel">
          <p class="intro">新しい見せ方が欲しいときは、下のテンプレートをコピーして、ローカルのymlを読めるAI（Claude Code 等）に貼り付けてください。新しいiframeビューとして追加できます。</p>
          __CARDS__
        </div>
        __META_PANELS__
        <div class="panel hidden" id="panel-help" role="tabpanel">
          <div class="help">
            <h2>このバンドルについて</h2>
            <ul>
              <li>これは単一ファイルではなく <code>index.html</code> + <code>views/</code> のフォルダ一式です。</li>
              <li>右ペインの iframe は <code>views/</code> 内の個別 HTML を読み込みます。タブでビューを切り替えられます。</li>
              <li>左ペイン = 別のビューを「追加」してもらうためのプロンプト集（チャットUIではありません）。</li>
            </ul>
            <h2>使い方</h2>
            <ul>
              <li>右上の <code>🌙 ダーク / ☀ ライト</code> でテーマを切り替え。</li>
              <li>テンプレートの <code>プロンプトをコピー</code> を押し、ローカルファイルを読めるAIに貼り付ける。</li>
              <li>返ってきた iframe HTML を <code>views/</code> に保存し、ビルドを再実行すると新しいタブとして増えます。</li>
            </ul>
            <h2>開き方の注意</h2>
            <ul>
              <li>Chrome/Edge は <code>file://</code> での iframe ローカル読み込みをブロックします。</li>
              <li>Firefox で開くか、フォルダ内で簡易サーバを起動してください（内容は外部通信しません）。</li>
            </ul>
            <h2>安全性</h2>
            <ul>
              <li>iframe は <code>sandbox="allow-scripts"</code>。親 DOM へはアクセスしません。</li>
              <li>ネットワーク通信・外部 CDN・ストレージ利用はありません。</li>
            </ul>
          </div>
        </div>
      </div>
    </section>
    <section class="pane pane-right" aria-label="図解プレビュー">
      <div class="preview-bar">
        <span class="dot" aria-hidden="true"></span>
        <div class="view-switcher" role="tablist" aria-label="ビュー切り替え">
          __VIEW_TABS__
        </div>
      </div>
      <div class="preview-wrap">
        <iframe class="preview" id="view-frame" title="理解対象の図解" sandbox="allow-scripts" src="__FIRST_VIEW_SRC__"></iframe>
      </div>
    </section>
  </main>
</div>
<script>
(function(){
  "use strict";
  function flash(btn){
    var original = btn.textContent;
    btn.textContent = "コピーしました";
    btn.classList.add("copied");
    setTimeout(function(){ btn.textContent = original; btn.classList.remove("copied"); }, 1400);
  }
  function fallbackCopy(text, btn){
    var ta = document.createElement("textarea");
    ta.value = text;
    ta.setAttribute("readonly", "");
    ta.style.position = "absolute";
    ta.style.left = "-9999px";
    document.body.appendChild(ta);
    ta.select();
    var ok = false;
    try { ok = document.execCommand("copy"); } catch (e) { ok = false; }
    document.body.removeChild(ta);
    if (ok) { flash(btn); } else { btn.textContent = "コピーできませんでした"; }
  }
  function copyText(text, btn){
    if (navigator.clipboard && navigator.clipboard.writeText){
      navigator.clipboard.writeText(text).then(function(){ flash(btn); },
        function(){ fallbackCopy(text, btn); });
    } else {
      fallbackCopy(text, btn);
    }
  }
  var buttons = document.querySelectorAll(".copy-btn");
  for (var i = 0; i < buttons.length; i++){
    buttons[i].addEventListener("click", function(){
      var target = document.getElementById(this.getAttribute("data-target"));
      if (!target) return;
      copyText(target.textContent, this);
    });
  }
  // left-pane tab switching (templates / yaml viewers / help)
  var tabs = document.querySelectorAll(".tab-btn");
  for (var j = 0; j < tabs.length; j++){
    tabs[j].addEventListener("click", function(){
      var panelId = this.getAttribute("data-panel");
      for (var k = 0; k < tabs.length; k++){
        tabs[k].classList.remove("active");
        tabs[k].setAttribute("aria-selected", "false");
      }
      this.classList.add("active");
      this.setAttribute("aria-selected", "true");
      var panels = document.querySelectorAll(".panel");
      for (var m = 0; m < panels.length; m++){ panels[m].classList.add("hidden"); }
      var active = document.getElementById(panelId);
      if (active) active.classList.remove("hidden");
    });
  }
  // theme: light default; toggle flips data-theme and re-propagates into the iframe
  function currentTheme(){
    return document.documentElement.getAttribute("data-theme") === "dark" ? "dark" : "light";
  }
  // right-pane view switching + theme propagation via the iframe URL hash.
  // We ALWAYS set the full src (file + "#theme=...") so the child re-reads the theme;
  // do NOT "optimize" this to mutate only location.hash — that is unreliable for a
  // cross-origin sandboxed child.
  var frame = document.getElementById("view-frame");
  var viewTabs = document.querySelectorAll(".view-tab");
  var currentFile = null;
  if (frame){
    var initial = frame.getAttribute("src") || "";
    currentFile = initial.split("#")[0];
  }
  function applyFrameSrc(){
    if (!frame || !currentFile) return;
    frame.setAttribute("src", currentFile + "#theme=" + currentTheme());
  }
  for (var v = 0; v < viewTabs.length; v++){
    viewTabs[v].addEventListener("click", function(){
      for (var w = 0; w < viewTabs.length; w++){
        viewTabs[w].classList.remove("active");
        viewTabs[w].setAttribute("aria-selected", "false");
      }
      this.classList.add("active");
      this.setAttribute("aria-selected", "true");
      currentFile = this.getAttribute("data-file");
      applyFrameSrc();
    });
  }
  var toggle = document.getElementById("theme-toggle");
  if (toggle){
    toggle.addEventListener("click", function(){
      var dark = currentTheme() === "dark";
      if (dark){ document.documentElement.removeAttribute("data-theme"); }
      else { document.documentElement.setAttribute("data-theme", "dark"); }
      toggle.textContent = dark ? "🌙 ダーク" : "☀ ライト";
      applyFrameSrc();
    });
  }
})();
</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# entry point
# ---------------------------------------------------------------------------

def build(args: argparse.Namespace) -> tuple[str, int]:
    bundle = Path(args.bundle)
    views_dir = bundle / "views"
    bundle.mkdir(parents=True, exist_ok=True)
    views_dir.mkdir(parents=True, exist_ok=True)

    manifest = load_manifest(bundle)
    used_ids = {v["id"] for v in manifest}

    # merge the new views into the manifest (append new, update existing in place)
    for label, path in parse_view_specs(args.view_html or []):
        doc = read_text(path)  # fail fast if the iframe doc is missing
        vid = slugify(label)
        existing = next((v for v in manifest if v["id"] == vid), None)
        if existing is not None:
            existing["label"] = label
            existing["_content"] = doc
        else:
            unique = vid
            n = 2
            while unique in used_ids:
                unique = f"{vid}-{n}"
                n += 1
            used_ids.add(unique)
            manifest.append({"id": unique, "label": label, "file": "", "_content": doc})

    if not manifest:
        raise SystemExit(
            "build_html.py: no views to build. Pass at least one --view-html "
            '"LABEL=PATH" (or build into a bundle that already has views.json).'
        )

    # recompute filenames from final order and write new/updated view files
    width = max(2, len(str(len(manifest))))
    for idx, v in enumerate(manifest, start=1):
        v["file"] = f"{idx:0{width}d}-{v['id']}.html"
        content = v.pop("_content", None)
        if content is not None:
            (views_dir / v["file"]).write_text(content, encoding="utf-8")
        elif not (views_dir / v["file"]).is_file():
            print(f"build_html.py: warning: manifest references missing file views/{v['file']}",
                  file=sys.stderr)

    # copy core/view yaml into the bundle (so their absolute paths are stable) and read
    # them back for the (display-only) viewer panels.
    def copy_yaml(src: str | None, name: str) -> tuple[str | None, str | None]:
        dest = bundle / name
        if src:
            dest.write_text(read_text(src), encoding="utf-8")
        if dest.is_file():
            return str(dest.resolve()), dest.read_text(encoding="utf-8")
        return None, None

    core_yaml_path, core_text = copy_yaml(args.core, "core.yaml")
    view_yaml_path, view_text = copy_yaml(args.view, "view.yaml")
    quiz_yaml_path, quiz_text = copy_yaml(args.quiz, "quiz.yaml")

    mapping = {
        "core_yaml_path": core_yaml_path or "(core.yaml は未指定)",
        "view_yaml_path": view_yaml_path or "(view.yaml は未指定)",
        "quiz_yaml_path": quiz_yaml_path or "(quiz.yaml は未指定)",
    }

    prompts = load_prompts(args.prompts)
    cards_html = render_cards(prompts, mapping)
    meta_tabs, meta_panels = render_meta(core_text, view_text, quiz_text)
    view_tabs = render_view_tabs(manifest)
    first_view_src = esc("views/" + manifest[0]["file"] + "#theme=light")

    title = args.title or "理解対象の図解"
    subtitle = args.subtitle or "iframe ビューを切り替えて理解する（ライト/ダーク対応）"

    document = HTML_TEMPLATE
    document = document.replace("__TITLE__", esc(title))
    document = document.replace("__SUBTITLE__", esc(subtitle))
    document = document.replace("__META_TABS__", meta_tabs)
    document = document.replace("__META_PANELS__", meta_panels)
    document = document.replace("__CARDS__", cards_html)
    document = document.replace("__VIEW_TABS__", view_tabs)
    document = document.replace("__FIRST_VIEW_SRC__", first_view_src)

    (bundle / "index.html").write_text(document, encoding="utf-8")
    write_manifest(bundle, manifest)
    return str(bundle), len(manifest)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="build_html.py",
        description=(
            "Build and incrementally grow a multi-file explainer bundle: a shell "
            "(index.html) plus switchable iframe views under views/. Re-running with a new "
            "--view-html appends a view. This is an assembler, not a fixed renderer."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "example:\n"
            "  python scripts/build_html.py \\\n"
            "    --bundle ./explainer-bundle \\\n"
            "    --core references/sample-core.yaml \\\n"
            "    --view references/sample-view.yaml \\\n"
            "    --quiz references/sample-quiz.yaml \\\n"
            "    --prompts references/sample-prompts.json \\\n"
            '    --view-html "エンジニア=references/sample-iframe.html" \\\n'
            '    --view-html "クイズ=references/sample-quiz-iframe.html"\n'
        ),
    )
    parser.add_argument("--bundle", required=True,
                        help="output bundle directory (created if missing)")
    parser.add_argument("--view-html", dest="view_html", action="append", default=[],
                        metavar="LABEL=PATH",
                        help='a view to add: tab LABEL plus path to its iframe HTML doc '
                             '(repeatable; appends/updates the bundle each run)')
    parser.add_argument("--core", help="path to core.yaml (copied in; abs path cited by prompts)")
    parser.add_argument("--view", help="path to view.yaml (copied in; abs path cited by prompts)")
    parser.add_argument("--quiz", help="path to quiz.yaml (optional; copied in; abs path "
                                       "cited by prompts)")
    parser.add_argument("--prompts", required=True,
                        help="path to prompts.json (array of prompt-template objects)")
    parser.add_argument("--title", help="optional header title for the shell")
    parser.add_argument("--subtitle", help="optional header subtitle for the shell")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    bundle, n_views = build(args)
    print(f"build_html.py: wrote bundle {bundle} ({n_views} view(s))")
    print("build_html.py: next, validate the bundle, e.g.:")
    print(f"  python scripts/validate_html.py {bundle}/index.html {bundle}/views/*.html")
    return 0


if __name__ == "__main__":
    sys.exit(main())
