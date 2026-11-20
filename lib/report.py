#!/usr/bin/env python3
"""Build an HTML report from the logs grade.sh leaves in its work folder.

usage: report.py PROJ DIR WORK LAST_OK  > report.html
"""
import html
import os
import re
import sys
from datetime import datetime

PROJ, DIR, WORK, LAST_OK = sys.argv[1:5]
ANSI = re.compile(r"\x1b\[[0-9;]*m")
esc = html.escape


def read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def parse_log(text):
    """Turn one exercise log into a list of items: (kind, title, detail_lines)."""
    items = []
    for raw in ANSI.sub("", text).splitlines():
        line = raw.rstrip()
        if not line.strip():
            continue
        s = line.strip()
        if s.startswith("➜"):
            continue
        if s.startswith("──"):
            items.append(("count", s.lstrip("─ ").strip(), []))
        elif s[0] in "✔✘⚠":
            kind = {"✔": "ok", "✘": "ko", "⚠": "warn"}[s[0]]
            items.append((kind, s[1:].strip(), []))
        elif items:
            items[-1][2].append(line[6:] if line.startswith("      ") else line.strip())
        else:
            items.append(("info", s, []))
    return items


def render_detail(lines):
    if not lines:
        return ""
    text = "\n".join(lines)
    # one-line form:  ควรได้: X  /  ได้จริง: Y
    exp = [l[len("ควรได้:"):].strip() for l in lines if l.startswith("ควรได้:")]
    got = [l[len("ได้จริง:"):].strip() for l in lines if l.startswith("ได้จริง:")]
    if exp and got and len(lines) == 2:
        return diff_table(exp[0], got[0])
    # block form (programs):  ควรได้ (cat -e):\n ...\n ได้จริง (cat -e):\n ...
    if lines[0].startswith("ควรได้") and any(l.startswith("ได้จริง") for l in lines):
        k = next(i for i, l in enumerate(lines) if l.startswith("ได้จริง"))
        e = "\n".join(l.strip() for l in lines[1:k])
        g = "\n".join(l.strip() for l in lines[k + 1:])
        return diff_table(e, g, note="(cat -e: $ คือท้ายบรรทัด)")
    return f"<pre class='log'>{esc(text)}</pre>"


def diff_table(exp, got, note=""):
    return (
        "<div class='diff'>"
        f"<div><div class='lbl ok'>ควรได้ {esc(note)}</div><pre>{esc(exp)}</pre></div>"
        f"<div><div class='lbl ko'>ได้จริง</div><pre>{esc(got)}</pre></div>"
        "</div>"
    )


rows = []
for line in read(os.path.join(WORK, "results.tsv")).splitlines():
    parts = line.split("\t")
    if len(parts) >= 3:
        rows.append(parts[:3])

passed = sum(1 for r in rows if r[1] == "OK")
total = len(rows)
pct = round(passed * 100 / total) if total else 0

chips, cards = [], []
for ex, res, files in rows:
    ok = res == "OK"
    chips.append(f"<a href='#{ex}' class='chip {'ok' if ok else 'ko'}'>{ex}</a>")
    items = parse_log(read(os.path.join(WORK, f"log_{ex}.txt")))
    lis = []
    count = ""
    for kind, title, detail in items:
        if kind == "count":
            count = title
            continue
        icon = {"ok": "✓", "ko": "✕", "warn": "!", "info": "·"}[kind]
        lis.append(
            f"<li class='{kind}'><span class='ic'>{icon}</span>"
            f"<div><div class='t'>{esc(title)}</div>{render_detail(detail)}</div></li>"
        )
    srcs = []
    for fname in files.split(","):
        path = os.path.join(DIR, ex, fname)
        if os.path.isfile(path):
            srcs.append(
                f"<details class='src'><summary>ดูโค้ด {esc(fname)}</summary>"
                f"<pre class='code'>{esc(read(path))}</pre></details>"
            )
    status = "ผ่าน" if ok else f"ไม่ผ่าน · {esc(res)}"
    cards.append(
        f"<details class='card {'ok' if ok else 'ko'}' id='{ex}' {'' if ok else 'open'}>"
        f"<summary><span class='dot'></span><b>{esc(ex)}</b>"
        f"<span class='files'>{esc(files.replace(',', ', '))}</span>"
        f"<span class='cnt'>{esc(count)}</span><span class='st'>{status}</span></summary>"
        f"<ul>{''.join(lis)}</ul>{''.join(srcs)}</details>"
    )

now = datetime.now().strftime("%d/%m/%Y %H:%M")
print(f"""<!DOCTYPE html>
<html lang="th"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(PROJ)} · ผลตรวจ</title>
<style>
:root{{--bg:#f6f7fb;--card:#fff;--ink:#1f2937;--mute:#6b7280;--line:#e5e7eb;--ok:#16a34a;--okbg:#dcfce7;--ko:#dc2626;--kobg:#fee2e2;--warn:#d97706;--accent:#2563eb}}
*{{box-sizing:border-box}}
body{{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans Thai",Sarabun,Arial,sans-serif;background:var(--bg);color:var(--ink);font-size:15px;line-height:1.5}}
.wrap{{max-width:980px;margin:0 auto;padding:28px 20px 60px}}
header{{display:flex;justify-content:space-between;align-items:flex-end;gap:16px;flex-wrap:wrap}}
h1{{margin:0;font-size:28px}} .sub{{color:var(--mute);font-size:13px;word-break:break-all}}
.sum{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:20px 0 14px}}
.box{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px 16px}}
.box .k{{color:var(--mute);font-size:12px;font-weight:600}} .box .v{{font-size:26px;font-weight:700}}
.bar{{height:8px;background:var(--line);border-radius:99px;overflow:hidden;margin-top:8px}}
.bar i{{display:block;height:100%;background:var(--ok);width:{pct}%}}
.chips{{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:18px}}
.chip{{padding:4px 12px;border-radius:99px;font-weight:600;font-size:13px;text-decoration:none}}
.chip.ok{{background:var(--okbg);color:var(--ok)}} .chip.ko{{background:var(--kobg);color:var(--ko)}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:14px;margin-bottom:10px;overflow:hidden}}
.card summary{{list-style:none;cursor:pointer;display:flex;align-items:center;gap:12px;padding:14px 16px}}
.card summary::-webkit-details-marker{{display:none}}
.dot{{width:10px;height:10px;border-radius:50%;flex:none}} .card.ok .dot{{background:var(--ok)}} .card.ko .dot{{background:var(--ko)}}
.files{{color:var(--mute);font-size:13px;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.cnt{{color:var(--mute);font-size:12px}}
.st{{font-size:12px;font-weight:700;padding:3px 10px;border-radius:99px}}
.card.ok .st{{background:var(--okbg);color:var(--ok)}} .card.ko .st{{background:var(--kobg);color:var(--ko)}}
.card.ko{{border-color:#fecaca}}
ul{{list-style:none;margin:0;padding:0 16px 10px;border-top:1px solid var(--line)}}
li{{display:flex;gap:10px;padding:8px 0;border-bottom:1px dashed var(--line)}} li:last-child{{border-bottom:0}}
.ic{{flex:none;width:20px;height:20px;border-radius:50%;display:grid;place-items:center;font-size:12px;font-weight:700;margin-top:1px}}
li.ok .ic{{background:var(--okbg);color:var(--ok)}} li.ko .ic{{background:var(--kobg);color:var(--ko)}}
li.warn .ic{{background:#fef3c7;color:var(--warn)}} li.info .ic{{background:var(--line);color:var(--mute)}}
li.ko .t{{color:var(--ko);font-weight:600}} li>div{{min-width:0;flex:1}}
pre{{margin:6px 0 0;padding:10px 12px;background:#0f172a;color:#e2e8f0;border-radius:10px;font:13px/1.45 ui-monospace,Menlo,Consolas,monospace;white-space:pre-wrap;word-break:break-all;max-height:320px;overflow:auto}}
.diff{{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:6px}}
.diff pre{{margin:0;background:#f8fafc;color:var(--ink);border:1px solid var(--line)}}
.lbl{{font-size:11px;font-weight:700;margin-bottom:3px}} .lbl.ok{{color:var(--ok)}} .lbl.ko{{color:var(--ko)}}
.src{{margin:0 16px 12px}} .src summary{{cursor:pointer;color:var(--accent);font-size:13px;font-weight:600;padding:4px 0}}
.code{{max-height:480px}}
.note{{color:var(--mute);font-size:12px;margin-top:24px}}
@media(max-width:640px){{.sum{{grid-template-columns:1fr}} .diff{{grid-template-columns:1fr}} .files{{display:none}}}}
</style></head><body><div class="wrap">
<header><div><h1>{esc(PROJ)} · ผลตรวจ</h1><div class="sub">{esc(DIR)}</div></div><div class="sub">{now}</div></header>
<div class="sum">
  <div class="box"><div class="k">ผ่าน</div><div class="v">{passed}/{total} ข้อ</div><div class="bar"><i></i></div></div>
  <div class="box"><div class="k">แบบ Moulinette ผ่านถึง</div><div class="v">{esc(LAST_OK)}</div></div>
  <div class="box"><div class="k">ข้อแรกที่พัง</div><div class="v">{esc(next((r[0] for r in rows if r[1] != 'OK'), '—'))}</div></div>
</div>
<div class="chips">{''.join(chips)}</div>
{''.join(cards)}
<p class="note">ตัวตรวจนี้ช่วยดูผลเท่านั้น ตอน evaluate ยังต้องอ่านโค้ดกับเพื่อน และให้เขาอธิบายตามใบประเมิน</p>
</div></body></html>""")
