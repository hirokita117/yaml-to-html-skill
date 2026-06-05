#!/usr/bin/env python3
"""validate_html.py

Scan generated HTML for unsafe / non-self-contained patterns.

The ``generate-explainer-html`` skill promises a single offline HTML file whose
iframe never talks to the network or reaches the parent page. This linter enforces that
promise. It is intentionally conservative: it flags string patterns, so a finding may
occasionally be a false positive (e.g. the word ``fetch`` in prose) — fix the wording or
the markup so the output stays unambiguously safe.

Important nuance
----------------
An ``<iframe>`` is REQUIRED by this skill, so the bare tag is never flagged. The bundle's
shell loads each view via a LOCAL relative ``src`` (e.g. ``src="views/01-x.html"``), which
is allowed. What is flagged is an iframe that loads a *remote* document via ``src`` with a
URL scheme or ``//`` prefix (a real network read).

Exit code
---------
0  -> no error-level findings
1  -> at least one error-level finding (problem locations are printed)
2  -> usage / file error
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# severity: "error" fails the run; "warn" is reported but does not fail.
# (name, severity, compiled-regex, explanation)
CHECKS = [
    ("external <script src>", "error",
     re.compile(r"<script\b[^>]*\bsrc\s*=", re.I),
     "external/remote script include is forbidden; inline <script> only"),
    ("external <iframe src>", "error",
     re.compile(r"<iframe\b[^>]*\bsrc\s*=\s*[\"']?\s*(?:[a-z][a-z0-9+.-]*:)?//", re.I),
     "iframe must not load a remote document; a local relative src (views/...) is allowed"),
    ("<object>", "error", re.compile(r"<object\b", re.I),
     "<object> can embed external/plugin content"),
    ("<embed>", "error", re.compile(r"<embed\b", re.I),
     "<embed> can embed external/plugin content"),
    ("external stylesheet <link>", "error",
     re.compile(r"<link\b[^>]*rel\s*=\s*[\"']?\s*stylesheet", re.I),
     "external CSS is forbidden; use inline <style> only"),
    ("fetch(", "error", re.compile(r"\bfetch\s*\("),
     "network call via fetch() is forbidden"),
    ("XMLHttpRequest", "error", re.compile(r"\bXMLHttpRequest\b"),
     "network call via XMLHttpRequest is forbidden"),
    ("WebSocket", "error", re.compile(r"\bWebSocket\b"),
     "network connection via WebSocket is forbidden"),
    ("localStorage", "error", re.compile(r"\blocalStorage\b"),
     "browser storage (localStorage) is forbidden"),
    ("sessionStorage", "error", re.compile(r"\bsessionStorage\b"),
     "browser storage (sessionStorage) is forbidden"),
    ("document.cookie", "error", re.compile(r"document\s*\.\s*cookie"),
     "cookie access is forbidden"),
    ("window.parent", "error", re.compile(r"window\s*\.\s*parent"),
     "reaching the parent frame is forbidden"),
    ("window.top", "error", re.compile(r"window\s*\.\s*top"),
     "reaching the top frame is forbidden"),
    ("target=\"_top\"", "error", re.compile(r"target\s*=\s*[\"']?_top", re.I),
     "top-level navigation via target=_top is forbidden"),
    ("http:// url", "error", re.compile(r"http://"),
     "plaintext http:// URL implies an external dependency"),
    ("https:// url", "error", re.compile(r"https://"),
     "plaintext https:// URL implies an external dependency"),
]


def scan_text(text: str):
    """Yield (severity, name, explanation, line_no, line_text) for every match."""
    lines = text.splitlines()
    for line_no, line in enumerate(lines, start=1):
        for name, severity, regex, explanation in CHECKS:
            if regex.search(line):
                yield severity, name, explanation, line_no, line.strip()


def validate_file(path: Path) -> tuple[int, int]:
    """Validate one file. Return (error_count, warn_count)."""
    if not path.is_file():
        print(f"validate_html.py: file not found: {path}", file=sys.stderr)
        return (-1, 0)

    text = path.read_text(encoding="utf-8", errors="replace")
    errors = 0
    warns = 0
    has_iframe = bool(re.search(r"<iframe\b", text, re.I))
    has_sandbox = bool(re.search(r"<iframe\b[^>]*\bsandbox\s*=", text, re.I))

    print(f"== {path} ==")
    for severity, name, explanation, line_no, snippet in scan_text(text):
        marker = "ERROR" if severity == "error" else "warn "
        if severity == "error":
            errors += 1
        else:
            warns += 1
        shown = snippet if len(snippet) <= 140 else snippet[:137] + "..."
        print(f"  [{marker}] line {line_no}: {name} — {explanation}")
        print(f"          > {shown}")

    if has_iframe and not has_sandbox:
        warns += 1
        print("  [warn ] iframe present without a sandbox attribute — add sandbox=\"allow-scripts\"")

    if errors == 0 and warns == 0:
        print("  OK: no unsafe patterns found.")
    else:
        print(f"  summary: {errors} error(s), {warns} warning(s).")
    print()
    return (errors, warns)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="validate_html.py",
        description=(
            "Check a generated HTML file for unsafe or non-self-contained patterns "
            "(external scripts/CSS/iframes, network APIs, storage, frame escape, URLs). "
            "A required sandboxed iframe is NOT flagged; an external-loading iframe is."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="example:\n  python scripts/validate_html.py sample-output.html\n",
    )
    parser.add_argument("files", nargs="+", help="HTML file(s) to validate")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="treat warnings as failures too (non-zero exit on any warning)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    total_errors = 0
    total_warns = 0
    for name in args.files:
        errors, warns = validate_file(Path(name))
        if errors < 0:
            return 2
        total_errors += errors
        total_warns += warns

    if total_errors:
        print(f"validate_html.py: FAILED — {total_errors} error(s) across {len(args.files)} file(s).")
        return 1
    if args.strict and total_warns:
        print(f"validate_html.py: FAILED (strict) — {total_warns} warning(s).")
        return 1
    print(f"validate_html.py: PASSED — {total_warns} warning(s), 0 error(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
