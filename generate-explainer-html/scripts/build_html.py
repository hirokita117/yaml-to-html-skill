#!/usr/bin/env python3
"""build_html.py

Assemble a single, self-contained HTML file for the ``generate-explainer-html`` skill.

This script is an *assembler*, not a renderer. It does NOT look at the meaning of
``core.yaml`` and turn it into a fixed diagram. The understanding UI is authored by an
AI (the iframe HTML) and merely embedded here. The script's job is limited to:

  * build the outer HTML shell (two-pane app, header, inline CSS)
  * embed the iframe HTML safely (sandboxed ``srcdoc``)
  * embed the prompt templates as copyable cards (inline copy-button JS)
  * embed core.yaml / view.yaml as viewable metadata panels
  * write everything out as one offline, dependency-free HTML file

Placeholder substitution
------------------------
Prompt strings inside ``prompts.json`` may contain ``{{core_yaml}}`` and ``{{view_yaml}}``.
Those two tokens are replaced with the raw contents of the ``--core`` / ``--view`` files so
that "regenerate" prompts carry the structured context with them. Any other ``{{...}}``
token (for example ``{{希望する表現}}``) is left untouched for the user to fill in.

Example
-------
    python scripts/build_html.py \
      --core core.yaml \
      --view view.yaml \
      --iframe iframe.html \
      --prompts prompts.json \
      --output output.html
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


def load_prompts(path: str) -> list[dict]:
    raw = read_text(path)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:  # pragma: no cover - user input error
        raise SystemExit(f"build_html.py: could not parse prompts JSON ({path}): {exc}")
    if not isinstance(data, list):
        raise SystemExit("build_html.py: prompts file must contain a JSON array")
    return data


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


def render_meta(core_text: str | None, view_text: str | None) -> tuple[str, str]:
    """Return (tab_buttons_html, panels_html) for the metadata views."""
    tabs: list[str] = []
    panels: list[str] = []
    if core_text is not None:
        tabs.append(
            '<button class="tab-btn" type="button" role="tab" aria-selected="false" '
            'data-panel="panel-core">core.yaml</button>'
        )
        panels.append(
            '<div class="panel hidden" id="panel-core" role="tabpanel">'
            '<p class="panel-note">理解対象の意味構造（UI ではなく意味）。</p>'
            f'<pre class="yaml-body">{esc(core_text)}</pre></div>'
        )
    if view_text is not None:
        tabs.append(
            '<button class="tab-btn" type="button" role="tab" aria-selected="false" '
            'data-panel="panel-view">view.yaml</button>'
        )
        panels.append(
            '<div class="panel hidden" id="panel-view" role="tabpanel">'
            '<p class="panel-note">この人にどう見せると分かりやすいかの方針。</p>'
            f'<pre class="yaml-body">{esc(view_text)}</pre></div>'
        )
    return "\n".join(tabs), "\n".join(panels)


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
  --bg:#0f1115; --panel:#171a21; --panel-2:#1f232c; --border:#2c313c;
  --text:#e6e9ef; --muted:#9aa3b2; --accent:#5aa9ff; --accent-2:#36c08f;
  --chip:#262b36; --danger:#ff6b6b; --radius:12px;
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
  padding:16px 20px;border-bottom:1px solid var(--border);
  background:linear-gradient(180deg,var(--panel-2),var(--panel));
  position:sticky;top:0;z-index:5;
}
.app-header h1{margin:0;font-size:18px;letter-spacing:.2px}
.app-header .subtitle{margin:4px 0 0;color:var(--muted);font-size:13px}
.app-header .source-label{color:var(--accent-2)}
.layout{display:grid;grid-template-columns:minmax(320px,440px) 1fr;gap:0;flex:1;min-height:0}
.pane{min-width:0;min-height:0}
.pane-left{
  border-right:1px solid var(--border);background:var(--panel);
  display:flex;flex-direction:column;max-height:calc(100vh - 64px);overflow:hidden;
}
.tabs{display:flex;gap:6px;padding:12px 12px 0;flex-wrap:wrap}
.tab-btn{
  background:var(--chip);color:var(--muted);border:1px solid var(--border);
  border-radius:999px;padding:6px 12px;font-size:12px;cursor:pointer;
}
.tab-btn:hover{color:var(--text)}
.tab-btn.active{background:var(--accent);color:#06121f;border-color:var(--accent);font-weight:600}
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
  background:#0c0e13;border:1px solid var(--border);border-radius:8px;
  padding:10px;margin:8px 0 0;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
  font-size:12px;white-space:pre-wrap;word-break:break-word;max-height:340px;overflow:auto;
}
.copy-btn{
  background:var(--accent);color:#06121f;border:0;border-radius:8px;
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
  padding:8px 14px;border-bottom:1px solid var(--border);color:var(--muted);font-size:12px;
  display:flex;align-items:center;gap:8px;
}
.preview-bar .dot{width:8px;height:8px;border-radius:50%;background:var(--accent-2)}
.preview-wrap{flex:1;min-height:0;padding:14px}
.preview{
  width:100%;height:100%;min-height:520px;border:1px solid var(--border);
  border-radius:var(--radius);background:#fff;
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
    <h1>__TITLE__</h1>
    <p class="subtitle">__SUBTITLE__</p>
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
          <p class="intro">右の図解を別の表現に変えたいときは、下のテンプレートをコピーして AI チャットに貼り付けてください。</p>
          __CARDS__
        </div>
        __META_PANELS__
        <div class="panel hidden" id="panel-help" role="tabpanel">
          <div class="help">
            <h2>このファイルについて</h2>
            <ul>
              <li>外部依存のない単一 HTML です。そのままブラウザで開けます。</li>
              <li>右ペイン（iframe）= 今回の理解対象に合わせた図解 UI。</li>
              <li>左ペイン = 別 AI に「別の表現で作り直して」と頼むためのプロンプト集。</li>
            </ul>
            <h2>使い方</h2>
            <ul>
              <li>テンプレートの <code>プロンプトをコピー</code> を押す。</li>
              <li>好みの AI チャットに貼り付ける。</li>
              <li>戻ってきた HTML をブラウザで開く。</li>
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
      <div class="preview-bar"><span class="dot" aria-hidden="true"></span>iframe 図解プレビュー（サンドボックス）</div>
      <div class="preview-wrap">
        <iframe class="preview" title="理解対象の図解" sandbox="allow-scripts" srcdoc="__IFRAME_SRCDOC__"></iframe>
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
})();
</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# entry point
# ---------------------------------------------------------------------------

def build(args: argparse.Namespace) -> str:
    core_text = read_text(args.core) if args.core else None
    view_text = read_text(args.view) if args.view else None
    iframe_html = read_text(args.iframe)
    prompts = load_prompts(args.prompts)

    mapping = {
        "core_yaml": core_text if core_text is not None else "(core.yaml は指定されていません)",
        "view_yaml": view_text if view_text is not None else "(view.yaml は指定されていません)",
    }

    cards_html = render_cards(prompts, mapping)
    meta_tabs, meta_panels = render_meta(core_text, view_text)

    title = args.title or "理解対象の図解"
    subtitle = args.subtitle or "iframe 内に図解、iframe 外に変換用プロンプト"

    document = HTML_TEMPLATE
    document = document.replace("__TITLE__", esc(title))
    document = document.replace("__SUBTITLE__", esc(subtitle))
    document = document.replace("__META_TABS__", meta_tabs)
    document = document.replace("__META_PANELS__", meta_panels)
    document = document.replace("__CARDS__", cards_html)
    # srcdoc must be escaped for an HTML attribute; textContent-style recovery is
    # not needed here because the browser parses srcdoc as a full document.
    document = document.replace("__IFRAME_SRCDOC__", html.escape(iframe_html, quote=True))
    return document


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="build_html.py",
        description=(
            "Assemble a single self-contained HTML file from an AI-authored iframe UI "
            "plus copyable prompt templates. This is an assembler, not a fixed renderer."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "example:\n"
            "  python scripts/build_html.py \\\n"
            "    --core references/sample-core.yaml \\\n"
            "    --view references/sample-view.yaml \\\n"
            "    --iframe references/sample-iframe.html \\\n"
            "    --prompts references/sample-prompts.json \\\n"
            "    --output sample-output.html\n"
        ),
    )
    parser.add_argument("--core", help="path to core.yaml (semantic structure; embedded as metadata)")
    parser.add_argument("--view", help="path to view.yaml (presentation strategy; embedded as metadata)")
    parser.add_argument("--iframe", required=True, help="path to the iframe HTML document (the explanation UI)")
    parser.add_argument("--prompts", required=True, help="path to prompts.json (array of prompt-template objects)")
    parser.add_argument("--output", required=True, help="path to write the assembled HTML file")
    parser.add_argument("--title", help="optional header title for the outer shell")
    parser.add_argument("--subtitle", help="optional header subtitle for the outer shell")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    document = build(args)
    out = Path(args.output)
    out.write_text(document, encoding="utf-8")
    size = len(document.encode("utf-8"))
    print(f"build_html.py: wrote {args.output} ({size} bytes)")
    print("build_html.py: next, run scripts/validate_html.py on the output before sharing it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
