"""Builds reports/q*.pdf from the recorded command logs, configs and screenshots.

usage: python3 lab/build_reports.py   (needs Google Chrome for HTML -> PDF)
"""
import html
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOGS = ROOT / "evidence" / "logs"
SHOTS = ROOT / "evidence" / "screenshots"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
REPO = "https://github.com/ksamirdev/ensp461-devops-lab3"

HEADER = {
    "course": "ENSP461 - DevOps &amp; Automation | Lab 3: Monitoring, Logging &amp; DevSecOps",
    "name": "Samir Kumar Gupta",
    "roll": "2301730243",
    "env": "Ubuntu 24.04 LTS (OrbStack VM, arm64)",
}

CSS = """
@page { size: A4; margin: 16mm 15mm; }
* { box-sizing: border-box; }
body { font: 10.5pt/1.45 "Helvetica Neue", Arial, sans-serif; color: #111; margin: 0; }
.meta { border-bottom: 1.5px solid #111; padding-bottom: 6px; margin-bottom: 14px; font-size: 9.5pt; }
.meta .course { font-weight: 700; font-size: 10.5pt; margin-bottom: 3px; }
.meta span { margin-right: 22px; }
h1 { font-size: 15pt; margin: 0 0 8px; }
h2 { font-size: 11.5pt; margin: 18px 0 6px; break-after: avoid; }
h3 { font-size: 10.5pt; margin: 12px 0 4px; break-after: avoid; }
.question { margin: 0 0 10px; }
p, li { margin: 0 0 6px; }
ul { padding-left: 18px; margin: 0 0 6px; }
pre { font: 8.2pt/1.38 Menlo, "DejaVu Sans Mono", monospace; background: #f5f5f4; border: 1px solid #ddd;
      border-radius: 4px; padding: 7px 9px; white-space: pre-wrap; word-break: break-all; margin: 0 0 8px; }
pre .cmd { color: #0b5394; font-weight: 700; }
.label { font-size: 8.5pt; color: #555; margin: 0 0 2px; }
figure { margin: 6px 0 12px; break-inside: avoid; }
figure img { display: block; width: auto; max-width: 100%; max-height: 105mm; margin: 0 auto; border: 1px solid #ccc; border-radius: 4px; }
figure.small img { width: 62%; }
figcaption { font-size: 8.5pt; color: #444; margin-top: 3px; text-align: center; }
table { break-inside: avoid; border-collapse: collapse; width: 100%; font-size: 9pt; margin: 0 0 10px; }
th, td { border: 1px solid #ccc; padding: 4px 6px; text-align: left; vertical-align: top; }
th { background: #f0f0ef; }
.keep { break-inside: avoid; }
"""


def esc(text):
    return html.escape(text, quote=False)


def blocks(log):
    """Split a rec.sh log into (command, output) pairs."""
    out, cmd, body = [], None, []
    for line in (LOGS / log).read_text().splitlines():
        if line.startswith("$ "):
            if cmd is not None:
                out.append((cmd, "\n".join(body).strip("\n")))
            cmd, body = line[2:], []
        else:
            body.append(line)
    if cmd is not None:
        out.append((cmd, "\n".join(body).strip("\n")))
    return out


def term(log, *needles, head=None, tail=None, label=None):
    """Terminal block with the recorded commands whose text contains any needle."""
    parts = []
    for cmd, output in blocks(log):
        if needles and not any(n in cmd for n in needles):
            continue
        lines = output.splitlines()
        if head and len(lines) > head:
            lines = lines[:head] + ["..."]
        if tail and len(lines) > tail:
            lines = ["..."] + lines[-tail:]
        parts.append(f'<span class="cmd">$ {esc(cmd)}</span>\n' + esc("\n".join(lines)))
    caption = f'<p class="label">{esc(label)}</p>' if label else ""
    joined = "\n".join(parts)
    return f"{caption}<pre>{joined}</pre>"


def config(path, label=None, start=None, end=None):
    """File contents, optionally from the line containing start up to (not including) the line containing end."""
    lines = (ROOT / path).read_text().splitlines()
    if start:
        lines = lines[next(i for i, l in enumerate(lines) if start in l):]
    if end:
        lines = lines[: next(i for i, l in enumerate(lines) if end in l)]
    return f'<p class="label">{esc(label or path)}</p><pre>{esc(chr(10).join(lines).strip())}</pre>'


def shot(name, caption, small=False):
    cls = ' class="small"' if small else ""
    src = (SHOTS / f"{name}.png").as_uri()
    return f'<figure{cls}><img src="{src}"><figcaption>{esc(caption)}</figcaption></figure>'


def bullets(*items):
    return "<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>"


def page(number, title, question, body):
    meta = (
        f'<div class="meta"><div class="course">{HEADER["course"]}</div>'
        f'<span>Name: {HEADER["name"]}</span><span>Roll No.: {HEADER["roll"]}</span>'
        f'<span>Environment: {HEADER["env"]}</span></div>'
    )
    intro = (
        f'<p class="question"><b>Question {number}:</b> {question}</p>'
        f"<p>All commands below were run on the lab machine and their output is copied verbatim from "
        f'the recorded logs in <code>evidence/logs/</code>. Repository: <a href="{REPO}">{REPO}</a>.</p>'
    )
    return (
        f'<!doctype html><html><head><meta charset="utf-8"><title>Q{number} {esc(title)}</title>'
        f"<style>{CSS}</style></head><body>{meta}<h1>Question {number} - {esc(title)}</h1>{intro}{body}</body></html>"
    )


def main():
    from report_content import REPORTS

    out_dir = ROOT / "reports"
    out_dir.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        for number, (slug, title, question, build) in REPORTS.items():
            src = Path(tmp) / f"{slug}.html"
            src.write_text(page(number, title, question, build()))
            pdf = out_dir / f"{slug}.pdf"
            subprocess.run(
                [CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                 "--allow-file-access-from-files", f"--print-to-pdf={pdf}", src.as_uri()],
                check=True, capture_output=True,
            )
            print(f"wrote {pdf.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
