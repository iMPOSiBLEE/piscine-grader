#!/usr/bin/env python3
"""piscine-grader: Shell00–01, C00–C13

grade                                   menu / เปิดเมนู
grade C03 <folder | git link> [--no-web] [--fix] [--peer]
grade update                            update / อัปเดต
"""
import datetime
import difflib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TESTS = os.path.join(HERE, "tests")
LIB = os.path.join(HERE, "lib")
TIMEOUT = int(os.environ.get("TIMEOUT", "10"))
CFLAGS = ["-Wall", "-Wextra", "-Werror"]


def _diag_flags():
    """gcc นับคอลัมน์ Tab เป็น 8 ช่อง ขอให้นับเป็นไบต์แทน (clang นับไบต์อยู่แล้ว)"""
    try:
        v = subprocess.run(["cc", "--version"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL).stdout.decode()
    except OSError:
        return []
    if "clang" in v.lower():
        return []
    ok = subprocess.run(["cc", "-fdiagnostics-column-unit=byte", "-x", "c", "-fsyntax-only", "-"], input=b"",
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
    return ["-fdiagnostics-column-unit=byte"] if ok else []


DIAG = _diag_flags()
TTY = sys.stdout.isatty() or os.environ.get("GRADER_COLOR") == "1"
CONFIG = os.path.join(os.path.expanduser("~"), ".config", "piscine-grader", "config.json")


def load_config():
    try:
        return json.load(open(CONFIG, encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_config(**kw):
    cfg = load_config()
    cfg.update(kw)
    os.makedirs(os.path.dirname(CONFIG), exist_ok=True)
    with open(CONFIG, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=1)


LANG = os.environ.get("GRADER_LANG") or load_config().get("lang", "th")


class Bi(str):
    """ข้อความที่จำได้ทั้งสองภาษา: ใช้เหมือน str ตามภาษาที่เลือก แต่ดึง .th / .en ได้เสมอ
    """
    th = en = ""

    def __new__(cls, th, en):
        s = super().__new__(cls, en if LANG == "en" else th)
        s.th, s.en = th, en
        return s


def L(th, en):
    """ข้อความตามภาษาที่เลือก"""
    return Bi(th, en)


def th_of(s):
    return getattr(s, "th", s) or ""


def en_of(s):
    return getattr(s, "en", s) or ""


def c(code, s):
    return f"\033[{code}m{s}\033[0m" if TTY else s


def green(s): return c("32", s)
def red(s): return c("31", s)
def yellow(s): return c("33", s)
def blue(s): return c("36", s)
def bold(s): return c("1", s)
def dim(s): return c("2", s)


KIND = {
    "file": ("📁", L("ไฟล์", "File")),
    "rule": ("🚫", L("กฎ", "Rule")),
    "norm": ("📏", "Norm"),
    "compile": ("🔧", L("คอมไพล์", "Compile")),
    "logic": ("🧠", L("ผลลัพธ์", "Output")),
    "crash": ("💥", L("พัง/ค้าง", "Crash/Hang")),
    "tip": ("💡", L("แนะนำ", "Tip")),     # ไม่ทำให้ตก
}
FAIL_KINDS = ("file", "rule", "norm")


# ───────────────────────── projects ─────────────────────────
def load_projects():
    projects = {}
    for p in sorted(os.listdir(TESTS)):
        f = os.path.join(TESTS, p, "files.txt")
        if not os.path.isfile(f):
            continue
        exs = []
        for line in open(f, encoding="utf-8"):
            parts = line.split()
            if len(parts) < 3:
                continue
            allowed = [] if len(parts) < 4 or parts[3] == "-" else parts[3].split(",")
            exs.append({"ex": parts[0], "type": parts[1], "files": parts[2].split(","), "allowed": allowed})
        projects[p] = exs
    return projects


PROJECTS = load_projects()


def detect_project(d):
    """เดาว่าเป็นโปรเจกต์ไหนจากชื่อไฟล์ในโฟลเดอร์"""
    found = set()
    try:
        for sub in os.listdir(d):
            sp = os.path.join(d, sub)
            if os.path.isdir(sp) and not sub.startswith("."):
                found.update(os.listdir(sp))
    except OSError:
        return []
    scores = []
    for p, exs in PROJECTS.items():
        expected = {f for e in exs for f in e["files"]}
        hit = len(found & expected)
        if hit:
            scores.append((hit / len(expected) + hit * 0.01, p))
    scores.sort(reverse=True)
    return [p for _, p in scores]


# ───────────────────────── helpers ─────────────────────────
def run(cmd, cwd=None, timeout=None, stdin=subprocess.DEVNULL):
    try:
        r = subprocess.run(cmd, cwd=cwd, stdin=stdin, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           timeout=timeout)
        return r.returncode, r.stdout.decode("utf-8", "replace")
    except subprocess.TimeoutExpired as e:
        out = (e.stdout or b"").decode("utf-8", "replace")
        return "TIMEOUT", out
    except FileNotFoundError:
        return "NOTFOUND", ""


def have(prog):
    return shutil.which(prog) is not None


def read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def char_diff(wrong, right):
    """อธิบายว่าชื่อผิดตรงตัวไหน"""
    out = []
    sm = difflib.SequenceMatcher(None, wrong, right)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "replace":
            out.append(L(f"ตัวที่ {i1 + 1}: '{wrong[i1:i2]}' ควรเป็น '{right[j1:j2]}'", f"char {i1 + 1}: '{wrong[i1:i2]}' should be '{right[j1:j2]}'"))
        elif op == "delete":
            out.append(L(f"ตัวที่ {i1 + 1}: มี '{wrong[i1:i2]}' เกินมา", f"char {i1 + 1}: extra '{wrong[i1:i2]}'"))
        elif op == "insert":
            out.append(L(f"ตัวที่ {i1 + 1}: ขาด '{right[j1:j2]}'", f"char {i1 + 1}: missing '{right[j1:j2]}'"))
    return ", ".join(out[:3])


def close_match(name, candidates, cutoff=0.7):
    m = difflib.get_close_matches(name, candidates, n=1, cutoff=cutoff)
    if m:
        return m[0]
    low = {x.lower(): x for x in candidates}
    return low.get(name.lower())


def issue(kind, title, why="", hint="", file=None, line=None, fixable=False, code=None):
    """title/hint เป็น Bi ได้ → เก็บไว้ทั้งไทยและอังกฤษ"""
    return {"kind": kind, "title": str(title), "why": str(why), "hint": str(hint), "file": file, "line": line,
            "fixable": fixable, "code": code,
            "title_th": th_of(title), "title_en": en_of(title), "hint_th": th_of(hint), "hint_en": en_of(hint),
            "why_en": en_of(why)}


def strip_thai(text):
    """ตัดคำไทยออกจากชื่อเคส เหลือส่วนโค้ด (ใช้ตอนเขียนภาษาอังกฤษ)"""
    if not text or not re.search("[฀-๿]", text):
        return text
    t = re.sub(r"[฀-๿]+(?:[ ]+[฀-๿0-9]+)*", "", text)
    t = re.sub(r"\(\s*[,.]?\s*\)", "", t)
    t = re.sub(r"\s{2,}", " ", t).strip(" ,.-:")
    return t if re.search(r"[A-Za-z0-9]", t) else "check"


# ───────────────────────── 42 header ─────────────────────────
def make_header(fname, login, mail, comment="c"):
    now = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    rows = [
        ("", "        :::      ::::::::   "),
        (fname, "      :+:      :+:    :+:   "),
        ("", "    +:+ +:+         +:+     "),
        (f"By: {login} <{mail}>", "  +#+  +:+       +#+        "),
        ("", "+#+#+#+#+#+   +#+           "),
        (f"Created: {now} by {login}", "     #+#    #+#             "),
        (f"Updated: {now} by {login}", "    ###   ########.fr       "),
    ]
    if comment == "c":
        top, side_l, side_r, edge = "/* " + "*" * 74 + " */", "/*", "*/", "/*" + " " * 76 + "*/"
    else:
        top, side_l, side_r, edge = "# " + "*" * 76 + " #", "#", "#", "#" + " " * 78 + "#"
    lines = [top, edge]
    for left, right in rows:
        room = 80 - len(side_r) - len(right) - len(side_l) - 3
        left = left[:room]
        body = side_l + "   " + left
        body = body + " " * (room - len(left)) + right + side_r
        lines.append(body)
    lines += [edge, top]
    return "\n".join(lines) + "\n\n"


def has_header(text):
    head = "\n".join(text.split("\n")[:12])
    return "By:" in head and "Created:" in head


def whoami():
    login = os.environ.get("USER") or "student"
    mail = os.environ.get("MAIL") or ""
    if "@" not in mail:
        mail = f"{login}@student.42bangkok.com"
    return login, mail


# ───────────────────────── C text utils ─────────────────────────
def code_mask(text):
    """แทนที่ comment/string ด้วยช่องว่าง (ความยาวเท่าเดิม) เพื่อให้นับวงเล็บได้ถูก"""
    out = list(text)
    i, n = 0, len(text)
    while i < n:
        if text.startswith("/*", i):
            j = text.find("*/", i + 2)
            j = n if j < 0 else j + 2
            for k in range(i, j):
                if out[k] != "\n":
                    out[k] = " "
            i = j
        elif text.startswith("//", i):
            j = text.find("\n", i)
            j = n if j < 0 else j
            for k in range(i, j):
                out[k] = " "
            i = j
        elif text[i] in "\"'":
            q = text[i]
            j = i + 1
            while j < n and text[j] != q and text[j] != "\n":
                j += 2 if text[j] == "\\" else 1
            for k in range(i + 1, min(j, n)):
                out[k] = " "
            i = j + 1
        else:
            i += 1
    return "".join(out)


def find_main(text):
    """คืน (บรรทัดเริ่ม, บรรทัดจบ) ของฟังก์ชัน main (นับจาก 0) หรือ None"""
    masked = code_mask(text)
    m = re.search(r"(^|\n)([^\n;{}]*\bmain\s*\([^)]*\)\s*)\{", masked)
    if not m:
        return None
    start = masked.count("\n", 0, m.start(2))
    depth, i = 0, m.end() - 1
    while i < len(masked):
        if masked[i] == "{":
            depth += 1
        elif masked[i] == "}":
            depth -= 1
            if depth == 0:
                break
        i += 1
    end = masked.count("\n", 0, i)
    return start, end


def main_line(text):
    r = find_main(text)
    if r:
        return r[0] + 1
    for i, l in enumerate(code_mask(text).split("\n")):
        if re.search(r"\bmain\s*\(", l):
            return i + 1
    return None


# ───────────────────────── fixers ─────────────────────────
TYPE_WORDS = r"(?:unsigned|signed|const|static|struct\s+\w+|long|short|int|char|void|float|double|size_t|t_\w+)"


def fix_remove_main(text):
    r = find_main(text)
    if not r:
        return text
    lines = text.split("\n")
    s, e = r
    while s > 0 and lines[s - 1].strip() == "":
        s -= 1
    del lines[s:e + 1]
    return "\n".join(lines)


def needs_header(fname):
    """Norm บังคับ 42 header แค่ไฟล์ .c และ .h (norminette ก็ตรวจแค่ 2 ชนิดนี้)"""
    return fname.endswith((".c", ".h"))


def fix_header(text, fname):
    if not needs_header(fname):
        return text          # .sh / Makefile: ไม่บังคับ และห้ามดัน #!/bin/sh ลงจากบรรทัดแรก
    login, mail = whoami()
    if text.startswith("/* ****") or text.startswith("# ****"):
        lines = text.split("\n")[11:]
        while lines and not lines[0].strip():
            lines.pop(0)
        text = "\n".join(lines)
    style = "c" if fname.endswith((".c", ".h")) else "sh"
    return make_header(fname, login, mail, style) + text.lstrip("\n")


def fix_add_include(text, header):
    if re.search(r"#\s*include\s*<" + re.escape(header) + ">", text):
        return text
    lines = text.split("\n")
    idx = 0
    if has_header(text):
        idx = 11
        while idx < len(lines) and lines[idx].strip() == "":
            idx += 1
    last_inc = None
    for i, l in enumerate(lines):
        if l.startswith("#include"):
            last_inc = i
    if last_inc is not None:
        lines.insert(last_inc + 1, f"#include <{header}>")
    else:
        lines[idx:idx] = [f"#include <{header}>", ""]
    return "\n".join(lines)


def reindent(text):
    """จัด indent ใหม่ด้วย Tab ตามระดับวงเล็บ (เฉพาะส่วนโค้ด ไม่แตะ header)"""
    lines = text.split("\n")
    masked = code_mask(text).split("\n")
    depth = 0
    pending = 0  # จำนวน if/while/else ซ้อนกันที่ไม่มี { ตามหลัง
    prev = ""
    paren = 0
    out = []
    for raw, m in zip(lines, masked):
        stripped = raw.strip()
        ms = m.strip()
        if not stripped or raw.startswith("/*") or raw.startswith("#") or (raw.startswith(" *") and "*/" in raw):
            out.append(raw if raw.startswith(("/*", "#")) else stripped)
            continue
        if paren > 0 or prev.endswith((",", "&&", "||", "+", "-", "*", "/", "(")) or not ms \
                or ms.startswith(("&&", "||")):
            out.append(raw)          # บรรทัดต่อจากบรรทัดก่อน: ไม่แตะ
            paren += ms.count("(") - ms.count(")")
            prev = ms or prev
            continue
        paren += ms.count("(") - ms.count(")")
        level = depth + pending
        if ms.startswith("}"):
            level = max(0, depth - 1)
        if ms.startswith("{"):
            level = depth
            pending = 0
        out.append("\t" * level + stripped)
        opens, closes = ms.count("{"), ms.count("}")
        depth = max(0, depth + opens - closes)
        if re.match(r"^(if|while|else if|else)\b", ms) and not ms.endswith(("{", ";")):
            pending += 1
        elif ms.endswith(";") or ms.endswith("}"):
            pending = 0
        prev = ms
    return "\n".join(out)


def fix_decl_tabs(text):
    """type  name  →  type<TAB>name (ฟังก์ชันและตัวแปร) และจัดตัวแปรให้ตรงคอลัมน์"""
    lines = text.split("\n")
    func_re = re.compile(r"^(" + TYPE_WORDS + r"(?:\s+" + TYPE_WORDS + r")*)[ \t]+(\**\w+\s*\()")
    var_re = re.compile(r"^(\t+)(" + TYPE_WORDS + r"(?:\s+" + TYPE_WORDS + r")*)[ \t]+(\**\w+(?:\[[^\]]*\])?\s*;)\s*$")
    # หัวฟังก์ชัน
    for i, l in enumerate(lines):
        m = func_re.match(l)
        if m and not l.rstrip().endswith(";"):
            lines[i] = m.group(1) + "\t" + l[m.end(1):].lstrip(" \t")
    # ตัวแปรในแต่ละฟังก์ชัน: จัดคอลัมน์ชื่อให้ตรงกัน
    i = 0
    while i < len(lines):
        if lines[i].strip() == "{" and not lines[i].startswith("\t"):
            j = i + 1
            block = []
            while j < len(lines):
                m = var_re.match(lines[j])
                if not m:
                    break
                block.append((j, m))
                j += 1
            if block:
                width = max(4 * len(m.group(1)) + len(m.group(2)) for _, m in block)
                col = (width // 4 + 1) * 4
                for j2, m in block:
                    cur = 4 * len(m.group(1)) + len(m.group(2))
                    tabs = max(1, (col - cur + 3) // 4)
                    lines[j2] = m.group(1) + m.group(2) + "\t" * tabs + m.group(3)
                after = block[-1][0] + 1
                if after < len(lines) and lines[after].strip() not in ("", "}"):
                    lines.insert(after, "")
            i = j
        i += 1
    return "\n".join(lines)


def fix_norm_text(text):
    """แก้เรื่อง norm ที่แก้ได้แบบปลอดภัย"""
    has_h = has_header(text)
    lines = text.split("\n")
    head, body = (lines[:11], lines[11:]) if has_h else ([], lines)
    t = "\n".join(body)
    # คีย์เวิร์ดต้องมีช่องว่างตามหลัง
    t = re.sub(r"\b(if|while|return|else if)\(", r"\1 (", t)
    # return x;  →  return (x);
    t = re.sub(r"\breturn\s+(?!\()([^;]+);", r"return (\1);", t)
    t = re.sub(r"\breturn\s+(\([^;]*\));", lambda m: "return " + m.group(1) + ";", t)
    # {  ที่อยู่ท้ายบรรทัดเดียวกับ ) หรือ else → ขึ้นบรรทัดใหม่
    t = re.sub(r"^([^\n{}]*\S)[ \t]*\{[ \t]*$", r"\1\n{", t, flags=re.M)
    t = re.sub(r"^([ \t]*)\}[ \t]*else\b", r"\1}\n\1else", t, flags=re.M)
    # ช่องว่างท้ายบรรทัด / บรรทัดว่างที่มีแต่ space
    t = "\n".join(l.rstrip() for l in t.split("\n"))
    t = reindent(t)
    t = fix_decl_tabs(t)
    # space ซ้อนกันกลางบรรทัด (นอก string)
    out = []
    for l in t.split("\n"):
        ind = len(l) - len(l.lstrip("\t"))
        rest = l[ind:]
        if '"' not in rest and "'" not in rest:
            rest = re.sub(r"(?<=\S) {2,}(?=\S)", " ", rest)
        out.append(l[:ind] + rest)
    t = "\n".join(out)
    # บรรทัดว่างติดกัน, บรรทัดว่างในฟังก์ชัน (ยกเว้นหลังประกาศตัวแปร), บรรทัดว่างหลัง #include
    t = re.sub(r"\n{3,}", "\n\n", t)
    t = re.sub(r"(#include[^\n]*\n)(?!#include|\n)", r"\1\n", t)
    t = t.strip("\n") + "\n"
    if has_h:
        return "\n".join(head) + "\n\n" + t.lstrip("\n")
    return t


def fix_semicolons(text, err_lines):
    """เติม ; ท้ายบรรทัดก่อนบรรทัดที่ compiler ฟ้อง"""
    lines = text.split("\n")
    for ln in sorted(set(err_lines), reverse=True):
        k = ln - 1
        for cand in (k, k - 1, k - 2):
            if 0 <= cand < len(lines):
                s = lines[cand].rstrip()
                if s and not s.endswith((";", "{", "}", ",", ")", "/", "*")) and not s.lstrip().startswith("#"):
                    lines[cand] = s + ";"
                    break
                if s.endswith(")") and re.search(r"\w\s*\(.*\)$", s.strip()) and not re.match(
                        r"^\s*(if|while|for)\b", s) and s.startswith("\t"):
                    lines[cand] = s + ";"
                    break
    return "\n".join(lines)


def fix_missing_comma(text, line, col):
    lines = text.split("\n")
    if 0 < line <= len(lines):
        l = lines[line - 1]
        for k in range(max(1, col - 3), min(len(l), col + 2)):
            if l[k] == " " and re.match(r"[\w\)\]'\"]", l[k - 1]) and k + 1 < len(l) and re.match(r"[\w&'\"(*-]", l[k + 1]):
                if l[k - 1] != ",":
                    lines[line - 1] = l[:k] + "," + l[k:]
                    break
    return "\n".join(lines)


def fix_char_quotes(text, line, name):
    lines = text.split("\n")
    if 0 < line <= len(lines) and len(name) == 1:
        lines[line - 1] = re.sub(r"(?<![\w'])" + re.escape(name) + r"(?![\w'])", f"'{name}'", lines[line - 1], count=1)
    return "\n".join(lines)


def fix_redeclared_param(text, line, name):
    lines = text.split("\n")
    if 0 < line <= len(lines) and re.match(r"^\s*" + TYPE_WORDS + r"\s+\**" + re.escape(name) + r"\b", lines[line - 1]):
        del lines[line - 1]
    return "\n".join(lines)


# ───────────────────────── norminette ─────────────────────────
NORM_TH = {
    "INVALID_HEADER": (L("ไม่มี 42 header หรือ header เสีย", "Missing or invalid 42 header"), L("ใส่ header ใหม่ (vim: :Stdheader)", "Add the header again (vim: :Stdheader)"), True),
    "SPACE_REPLACE_TAB": (L("ใช้ Space ในที่ที่ต้องเป็น Tab", "Space used where a Tab is required"), L("ระหว่างชนิดตัวแปรกับชื่อ และย่อหน้า ต้องใช้ Tab", "Use Tab between type and name, and for indentation"), True),
    "TAB_REPLACE_SPACE": (L("ใช้ Tab ในที่ที่ต้องเป็น Space", "Tab used where a Space is required"), "", True),
    "SPACE_BEFORE_FUNC": (L("ระหว่างชนิดกับชื่อฟังก์ชันต้องเป็น Tab", "Tab required between return type and function name"), L("เช่น void<Tab>ft_putchar(...)", "e.g. void<Tab>ft_putchar(...)"), True),
    "TOO_FEW_TAB": (L("ย่อหน้าไม่พอ", "Not enough indentation"), L("ข้างใน { } ต้องย่อหน้าเพิ่ม 1 Tab ต่อชั้น", "Inside { } indent one more Tab per level"), True),
    "TOO_MANY_TAB": (L("ย่อหน้าเกิน", "Too much indentation"), "", True),
    "MIXED_SPACE_TAB": (L("ย่อหน้าปน Space กับ Tab", "Indentation mixes Spaces and Tabs"), L("ใช้ Tab อย่างเดียว", "Use Tabs only"), True),
    "SPC_BEFORE_NL": (L("มี Space ท้ายบรรทัด", "Space at end of line"), L("ลบช่องว่างท้ายบรรทัด", "Remove trailing spaces"), True),
    "SPACE_EMPTY_LINE": (L("บรรทัดว่างมี Space/Tab ค้าง", "Empty line contains Spaces/Tabs"), "", True),
    "CONSECUTIVE_NEWLINES": (L("มีบรรทัดว่างติดกันหลายบรรทัด", "Several empty lines in a row"), L("เหลือบรรทัดว่างได้แค่ 1", "Keep only one empty line"), True),
    "CONSECUTIVE_SPC": (L("มี Space ติดกันหลายตัว", "Several spaces in a row"), "", True),
    "EMPTY_LINE_EOF": (L("มีบรรทัดว่างท้ายไฟล์", "Empty line at end of file"), "", True),
    "EMPTY_LINE_FUNCTION": (L("มีบรรทัดว่างในฟังก์ชัน", "Empty line inside function"), L("บรรทัดว่างในฟังก์ชันมีได้ที่เดียวคือหลังประกาศตัวแปร", "The only empty line allowed in a function is after the variable declarations"), True),
    "BRACE_NEWLINE": (L("{ ต้องอยู่บรรทัดใหม่ของตัวเอง", "{ must be on its own line"), "", True),
    "BRACE_SHOULD_EOL": (L("หลัง { หรือ } ต้องขึ้นบรรทัดใหม่", "Line break required after { or }"), "", True),
    "RETURN_PARENTHESIS": (L("ค่าที่ return ต้องอยู่ในวงเล็บ", "Return value must be in parentheses"), L("เขียนเป็น return (x);", "write return (x);"), True),
    "SPACE_AFTER_KW": (L("หลัง if/while/return ต้องเว้น 1 Space", "Put one space after if/while/return"), L("เขียนเป็น if (...)", "write if (...)"), True),
    "NL_AFTER_VAR_DECL": (L("หลังประกาศตัวแปรต้องเว้น 1 บรรทัด", "Empty line required after variable declarations"), "", True),
    "NL_AFTER_PREPROC": (L("หลัง #include ต้องเว้นบรรทัด", "Empty line required after #include"), "", True),
    "MISALIGNED_VAR_DECL": (L("ชื่อตัวแปรไม่ตรงคอลัมน์เดียวกัน", "Variable names are not aligned"), L("ใช้ Tab จัดชื่อตัวแปรให้ตรงกัน", "Align the names with Tabs"), True),
    "MISALIGNED_FUNC_DECL": (L("ชื่อฟังก์ชันไม่ตรงคอลัมน์", "Function names are not aligned"), "", True),
    "SPC_AFTER_OPERATOR": (L("หลังเครื่องหมาย (+ - = ...) ต้องเว้น Space", "Space required after operator (+ - = ...)"), L("เช่น a = b + 1", "e.g. a = b + 1"), False),
    "SPC_BFR_OPERATOR": (L("ก่อนเครื่องหมาย (+ - = ...) ต้องเว้น Space", "Space required before operator (+ - = ...)"), "", False),
    "NO_SPC_AFR_OPR": (L("หลังเครื่องหมายห้ามเว้น Space", "No space allowed after this operator"), "", False),
    "NO_SPC_BFR_OPR": (L("ก่อนเครื่องหมายห้ามเว้น Space", "No space allowed before this operator"), "", False),
    "SPC_AFTER_PAR": (L("หลัง ( ห้ามเว้น Space", "No space after ("), "", False),
    "SPC_BFR_PAR": (L("ก่อน ) ห้ามเว้น Space", "No space before )"), "", False),
    "NO_ARGS_VOID": (L("ฟังก์ชันที่ไม่รับค่าต้องเขียน (void)", "A function without parameters must be declared (void)"), L("เช่น void ft_print_alphabet(void)", "e.g. void ft_print_alphabet(void)"), False),
    "TOO_MANY_LINES": (L("ฟังก์ชันยาวเกิน 25 บรรทัด", "Function longer than 25 lines"), L("แยกบางส่วนออกเป็นฟังก์ชันย่อย", "Move part of it into a helper function"), False),
    "TOO_MANY_FUNCS": (L("มีฟังก์ชันเกิน 5 ตัวในไฟล์", "More than 5 functions in the file"), "", False),
    "TOO_MANY_VARS_FUNC": (L("ประกาศตัวแปรเกิน 5 ตัวในฟังก์ชัน", "More than 5 variables in the function"), L("ย้ายบางส่วนไปฟังก์ชันย่อย", "Move some work into a helper function"), False),
    "TOO_MANY_ARGS": (L("ฟังก์ชันรับ argument เกิน 4 ตัว", "More than 4 parameters"), "", False),
    "LINE_TOO_LONG": (L("บรรทัดยาวเกิน 80 ตัวอักษร", "Line longer than 80 characters"), L("ตัดขึ้นบรรทัดใหม่", "Break the line"), False),
    "FORBIDDEN_CS": (L("ใช้คำสั่งต้องห้าม (for, do...while, switch, goto)", "Forbidden statement (for, do...while, switch, goto)"), L("เปลี่ยนเป็น while", "Use while instead"), False),
    "TERNARY_FBIDDEN": (L("ห้ามใช้ ? : (ternary)", "Ternary ? : is forbidden"), L("เปลี่ยนเป็น if/else", "Use if/else instead"), False),
    "VAR_DECL_START_FUNC": (L("ต้องประกาศตัวแปรไว้ต้นฟังก์ชันเท่านั้น", "Declare variables at the top of the function only"), "", False),
    "DECL_ASSIGN_LINE": (L("ห้ามประกาศตัวแปรพร้อมกำหนดค่า", "Declaration and assignment on the same line is forbidden"), L("แยกเป็น int i; แล้วค่อย i = 0;", "Write int i; then i = 0;"), False),
    "MULT_DECL_LINE": (L("ห้ามประกาศหลายตัวแปรในบรรทัดเดียว", "Only one declaration per line"), "", False),
    "TOO_MANY_INSTR": (L("มีหลายคำสั่งในบรรทัดเดียว", "Several instructions on one line"), L("1 บรรทัด 1 คำสั่ง", "One instruction per line"), False),
    "WRONG_SCOPE_COMMENT": (L("ห้ามเขียน comment ข้างในฟังก์ชัน", "Comments are not allowed inside functions"), L("ย้าย comment ไปไว้นอกฟังก์ชัน", "Move the comment outside the function"), False),
    "FORBIDDEN_CHAR_NAME": (L("ชื่อตัวแปร/ฟังก์ชันต้องเป็นตัวเล็ก ตัวเลข หรือ _ เท่านั้น", "Names must use lowercase letters, digits or _ only"), "", False),
    "USER_DEFINED_TYPEDEF": (L("ชื่อ typedef ต้องขึ้นต้นด้วย t_", "typedef names must start with t_"), "", False),
    "STRUCT_TYPE_NAMING": (L("ชื่อ struct ต้องขึ้นต้นด้วย s_", "struct names must start with s_"), "", False),
    "HEADER_PROT_ALL": (L("header ต้องมี #ifndef ... #define ... #endif ป้องกัน include ซ้ำ", "Header needs #ifndef ... #define ... #endif protection"), "", False),
    "HEADER_PROT_NAME": (L("ชื่อ macro ป้องกัน header ต้องเป็น ชื่อไฟล์_H ตัวใหญ่", "Guard macro must be FILENAME_H in capitals"), L("เช่น FT_H", "e.g. FT_H"), False),
    "PREPROC_CONSTANT": (L("#define ต้องเป็นค่าคงที่เท่านั้น", "#define must be a constant"), "", False),
    "MACRO_NAME_CAPITAL": (L("ชื่อ macro ต้องเป็นตัวใหญ่", "Macro names must be uppercase"), "", False),
    "PREPROC_BAD_INDENT": (L("#define ใน #ifndef ต้องเว้น 1 Space หลัง #", "Inside #ifndef write '# define' (space after #)"), L("เขียนเป็น # define", "write # define"), False),
    "INCLUDE_START_FILE": (L("#include ต้องอยู่ต้นไฟล์", "#include must be at the top of the file"), "", False),
    "GLOBAL_VAR_DETECTED": (L("ห้ามใช้ตัวแปร global", "Global variables are forbidden"), "", False),
    "EXP_PARENTHESIS": (L("ต้องมีช่องว่างก่อน (", "Space required before ("), "", False),
}


def parse_norm(out, fname):
    issues = []
    for m in re.finditer(r"Error:\s+(\w+)\s+\(line:\s*(\d+),\s*col:\s*(\d+)\):\s*(.*)", out):
        code, ln, _col, msg = m.group(1), int(m.group(2)), m.group(3), re.sub(r"\x1b\[[0-9;]*m", "", m.group(4))
        th = NORM_TH.get(code)
        title = th[0] if th else msg.strip()
        hint = th[1] if th else ""
        issues.append(issue("norm", title, why=f"{code}: {msg.strip()}", hint=hint, file=fname, line=ln,
                            fixable=bool(th and th[2]), code=code))
    return issues


# ───────────────────────── compiler messages ─────────────────────────
def explain_cc(msg):
    """แปลข้อความ error ของ gcc/clang เป็นคำอธิบายภาษาไทย → (title, hint, fix_kind)"""
    m = msg
    rules = [
        (r"expected ';'|expected ',' or ';'", L("ลืม ; ท้ายคำสั่ง", "Missing ; at the end of a statement"), L("ใส่ ; ที่ท้ายบรรทัดก่อนหน้าบรรทัดนี้", "Add ; at the end of the previous line"), "semicolon"),
        (r"expected '\)' before (numeric constant|'&'|'\w+'|string constant|character constant)|expected ',' or '\)'|^expected '\)'$",
         L("ลืม , คั่นระหว่างค่าที่ส่งให้ฟังก์ชัน", "Missing , between function arguments"), L("เช่น write(1, &c, 1) ต้องมี , ครบทุกช่อง", "e.g. write(1, &c, 1) needs every comma"), "comma"),
        (r"implicit declaration of function '?write'?|call to undeclared function 'write'",
         L("เรียก write แต่ไม่ได้ #include <unistd.h>", "write is used but <unistd.h> is not included"), L("ใส่ #include <unistd.h> ไว้บนสุด", "Add #include <unistd.h> at the top"), "inc_unistd"),
        (r"implicit declaration of function '?(malloc|free)'?|call to undeclared (library )?function '(malloc|free)'",
         L("เรียก malloc/free แต่ไม่ได้ #include <stdlib.h>", "malloc/free used but <stdlib.h> is not included"), L("ใส่ #include <stdlib.h>", "Add #include <stdlib.h>"), "inc_stdlib"),
        (r"'NULL' undeclared|undeclared identifier 'NULL'",
         L("ใช้ NULL แต่ไม่ได้ #include <stdlib.h>", "NULL used but <stdlib.h> is not included"), L("ใส่ #include <stdlib.h> หรือใช้ 0 แทน", "Add #include <stdlib.h> or use 0"), "inc_stdlib"),
        (r"implicit declaration of function|call to undeclared function",
         L("เรียกฟังก์ชันที่ยังไม่ได้ประกาศ", "Calling a function that is not declared"), L("ต้องเขียนฟังก์ชันนั้นไว้ข้างบน หรือใส่ prototype", "Define the function above, or add a prototype"), None),
        (r"redeclared as different kind of symbol|redefinition of '(\w+)'.*|redefinition of parameter",
         L("ประกาศตัวแปรชื่อซ้ำกับ parameter", "Variable redeclares a parameter"), L("ตัวแปรนี้มีมาให้แล้วในวงเล็บของฟังก์ชัน ไม่ต้องประกาศใหม่", "This variable already comes from the function's parameters; do not declare it again"), "redecl"),
        (r"'(\w+)' undeclared|use of undeclared identifier '(\w+)'",
         L("ใช้ชื่อที่ไม่มีอยู่ (ยังไม่ได้ประกาศ หรือพิมพ์ผิด)", "Unknown name (not declared or misspelled)"),
         L("ถ้าหมายถึงตัวอักษร ต้องใส่ ' ' เช่น 'A' / ถ้าเป็นตัวแปร ต้องประกาศก่อน", "A single character needs quotes like 'A'; a variable must be declared first"), "undeclared"),
        (r"unused variable", L("ประกาศตัวแปรแล้วไม่ได้ใช้ (-Werror ถือว่าเป็น error)", "Unused variable (-Werror makes it an error)"), L("ลบตัวแปรนั้นทิ้ง", "Remove the variable"), None),
        (r"unused parameter", L("parameter ไม่ได้ถูกใช้เลย", "Unused parameter"), L("ใช้มันในฟังก์ชัน หรือเขียน (void)ชื่อ;", "Use it, or write (void)name;"), None),
        (r"conflicting types", L("prototype ไม่ตรงกับตัวฟังก์ชัน", "Prototype does not match the function"), L("ชนิดของ return/parameter ต้องตรงกันทั้งสองที่", "Return and parameter types must match"),
         None),
        (r"control reaches end of non-void function|non-void function does not return",
         L("ฟังก์ชันที่ต้องคืนค่า แต่บางทางไม่มี return", "Non-void function without return on some path"), L("ใส่ return (...); ให้ครบทุกทาง", "Add return (...); on every path"), None),
        (r"expected declaration or statement at end of input|expected '}'", L("ปีกกา { } ไม่ครบคู่", "Unbalanced { }"),
         L("นับ { กับ } ให้เท่ากัน", "Balance your { and }"), None),
        (r"expected identifier or '\('|expected expression", L("เขียนคำสั่งผิดรูปแบบตรงนี้", "Syntax error here"),
         L("ดูเครื่องหมายรอบ ๆ ตำแหน่งนี้ (วงเล็บ, ;, ,)", "Check the symbols around this spot (parentheses, ;, ,)"), None),
        (r"comparison between pointer and integer|makes integer from pointer|makes pointer from integer",
         L("ใช้ pointer กับตัวเลขปนกัน", "Mixing pointers and integers"), L("ตัวอักษรเดียวใช้ ' ' ส่วนข้อความใช้ \" \"", "One character uses ' ', text uses \\\" \\\""), None),
        (r"too few arguments", L("ส่งค่าให้ฟังก์ชันไม่ครบ", "Too few arguments"), "", None),
        (r"too many arguments", L("ส่งค่าให้ฟังก์ชันเกิน", "Too many arguments"), "", None),
        (r"suggest parentheses", L("ควรใส่วงเล็บครอบเงื่อนไข", "Add parentheses around the condition"), L("เช่น if ((a = b))", "e.g. if ((a = b))"), None),
        (r"is used uninitialized|may be used uninitialized", L("ใช้ตัวแปรก่อนกำหนดค่า", "Variable used before it is set"), L("กำหนดค่าเริ่มต้นก่อนใช้", "Initialise it first"),
         None),
        (r"stray '\\\d+'|stray '", L("มีตัวอักษรแปลก ๆ ในโค้ด (อาจเป็นสระไทยหรือเครื่องหมายพิเศษ)", "Strange character in the code (non-ASCII)"), "", None),
    ]
    for pat, title, hint, kind in rules:
        mm = re.search(pat, m)
        if mm:
            return title, hint, kind, mm
    return m, "", None, None


def parse_cc(out, fname):
    out = out.replace("\u2018", "'").replace("\u2019", "'")
    issues, fixes = [], []
    seen = set()
    for m in re.finditer(r"^([^\s:]+):(\d+):(\d+):\s*(fatal error|error|warning):\s*(.*)$", out, re.M):
        path, ln, col, msg = m.group(1), int(m.group(2)), int(m.group(3)), m.group(5)
        if not path.endswith(os.path.basename(fname)) and "/" not in path:
            pass
        title, hint, kind, mm = explain_cc(msg)
        key = (ln, title)
        if key in seen:
            continue
        seen.add(key)
        fixable = kind in ("semicolon", "comma", "inc_unistd", "inc_stdlib", "redecl", "undeclared")
        name = None
        if kind in ("redecl", "undeclared") and mm:
            name = next((g for g in mm.groups() if g), None)
            q = re.search(r"'(\w+)'", msg)
            name = q.group(1) if q else name
            if kind == "undeclared" and (not name or len(name) != 1):
                fixable = False
        q = re.search(r"'(\w+)'", msg)
        if q and kind not in ("semicolon", "comma") and q.group(1) not in title:
            title = L(f"{th_of(title)} → '{q.group(1)}'", f"{en_of(title)} → '{q.group(1)}'")
        issues.append(issue("compile", title, why=msg, hint=hint, file=os.path.basename(fname), line=ln,
                            fixable=fixable, code="cc"))
        if fixable:
            fixes.append((kind, ln, col, name))
    return issues, fixes


def apply_cc_fixes(text, fixes):
    redecl = {ln for k, ln, _c, n in fixes if k == "redecl" and n}
    fixes = [f for f in fixes if not (f[0] == "undeclared" and f[1] in redecl)]
    semis = [ln for k, ln, _c, _n in fixes if k == "semicolon" and (ln - 1) not in redecl and ln not in redecl]
    # ทำจากล่างขึ้นบนเพื่อไม่ให้เลขบรรทัดเลื่อน
    for kind, ln, col, name in sorted(fixes, key=lambda f: -f[1]):
        if kind == "comma":
            text = fix_missing_comma(text, ln, col)
        elif kind == "redecl" and name:
            text = fix_redeclared_param(text, ln, name)
        elif kind == "undeclared" and name:
            text = fix_char_quotes(text, ln, name)
    if semis:
        text = fix_semicolons(text, semis)
    for kind, *_ in fixes:
        if kind == "inc_unistd":
            text = fix_add_include(text, "unistd.h")
        if kind == "inc_stdlib":
            text = fix_add_include(text, "stdlib.h")
    return text


# ───────────────────────── logic hints ─────────────────────────
def load_hints(proj):
    p = os.path.join(TESTS, proj, "hints.json")
    try:
        return json.load(open(p, encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def guess_hints(proj, ex, cases, status):
    hints = []
    table = load_hints(proj).get(ex, [])
    bad = [cs for cs in cases if not cs["ok"]]
    for h in table:
        pat = h.get("match", "*")
        if pat == "*" or any(re.search(pat, cs["name"] + " " + cs.get("exp", "") + " " + cs.get("got", ""), re.I)
                             for cs in bad):
            hints.append(L(h["hint"], h.get("hint_en", h["hint"])))
    for cs in bad:
        e, g = cs.get("exp", ""), cs.get("got", "")
        if g in ('""', "") and e not in ('""', ""):
            hints.append(L("ฟังก์ชันไม่ได้พิมพ์/คืนอะไรออกมาเลย เช็กว่าเรียก write หรือ return ค่าจริงไหม", "The function printed/returned nothing. Check that write or return really happens"))
        elif g.startswith(e.rstrip('"')) and len(g) > len(e):
            hints.append(L("ผลลัพธ์มีของเกินท้าย เช่น , หรือขึ้นบรรทัดใหม่เกิน", "Output has extra characters at the end, e.g. a comma or newline"))
        elif e.startswith(g.rstrip('"')) and len(e) > len(g):
            hints.append(L("ผลลัพธ์ขาดท้าย เช่น ลืมตัวสุดท้าย หรือเงื่อนไข while หยุดเร็วไป 1 รอบ", "Output is missing the end: last item forgotten or the while stops one step early"))
    if status == "TIMEOUT":
        hints.append(L("โปรแกรมวนไม่จบ: ลืมเพิ่มค่า i++ หรือเงื่อนไข while ไม่มีวันเป็นเท็จ", "Infinite loop: i++ forgotten or the while condition never becomes false"))
    if status == "CRASH":
        hints.append(L("โปรแกรมพัง (segfault): อ่านเกินขอบ string/array, ใช้ pointer ที่เป็น NULL หรือลืม malloc", "Crash (segfault): reading past a string/array, using a NULL pointer, or missing malloc"))
    out = []
    for h in hints:
        if h not in out:
            out.append(h)
    return out[:4]


def en_case(text):
    """โหมดอังกฤษ: ตัดคำอธิบายภาษาไทยในชื่อเคสออก เหลือส่วนโค้ด"""
    return strip_thai(text) if LANG == "en" else text


def parse_cases(out):
    cases = []
    lines = re.sub(r"\x1b\[[0-9;]*m", "", out).split("\n")
    i = 0
    while i < len(lines):
        s = lines[i].strip()
        if s.startswith("✔"):
            cases.append({"name": s[1:].strip(), "ok": True})
        elif s.startswith("✘"):
            cs = {"name": s[1:].strip(), "ok": False}
            j = i + 1
            while j < len(lines) and lines[j].startswith("      "):
                t = lines[j].strip()
                if t.startswith("ควรได้"):
                    cs["exp"] = t.split(":", 1)[1].strip() if ":" in t else ""
                    if t.endswith("(cat -e):"):
                        block = []
                        j += 1
                        while j < len(lines) and lines[j].startswith("      ") and not lines[j].strip().startswith("ได้จริง"):
                            block.append(lines[j].strip())
                            j += 1
                        cs["exp"] = "\n".join(block)
                        continue
                elif t.startswith("ได้จริง"):
                    cs["got"] = t.split(":", 1)[1].strip() if ":" in t else ""
                    if t.endswith("(cat -e):"):
                        block = []
                        j += 1
                        while j < len(lines) and lines[j].startswith("      "):
                            block.append(lines[j].strip())
                            j += 1
                        cs["got"] = "\n".join(block)
                        continue
                j += 1
            i = j - 1
            cases.append(cs)
        i += 1
    return cases


def PROJ_SPEC_WILD(spec, proj):
    return any(e["ex"] == spec["ex"] and e["files"] == ["*"] for e in PROJECTS.get(proj, []))


# ───────────────────────── program tests (C10, C11 do-op) ─────────────────────────
def make_fixtures(d):
    import random
    rnd = random.Random(42)
    with open(os.path.join(d, "small.txt"), "w") as f:
        f.write("Hello 42\nsecond line\n")
    with open(os.path.join(d, "big.txt"), "w") as f:
        f.write("".join(f"line {i} " + "x" * rnd.randint(0, 80) + "\n" for i in range(3000)))
    with open(os.path.join(d, "bin.dat"), "wb") as f:
        f.write(bytes(range(256)) + b"A" * 64 + b"\x00\x01" * 20 + b"end")
    open(os.path.join(d, "empty.txt"), "w").close()
    os.makedirs(os.path.join(d, "dir"), exist_ok=True)
    with open(os.path.join(d, "noread.txt"), "w") as f:
        f.write("secret\n")
    os.chmod(os.path.join(d, "noread.txt"), 0)


def hexdump_C(data):
    out, prev, star, off = [], None, False, 0
    while off < len(data):
        chunk = data[off:off + 16]
        if prev is not None and chunk == prev and len(chunk) == 16:
            if not star:
                out.append("*\n")
                star = True
        else:
            star = False
            g1 = "".join(f"{b:02x} " for b in chunk[:8]).ljust(24)
            g2 = "".join(f"{b:02x} " for b in chunk[8:]).ljust(24)
            out.append(f"{off:08x}  {g1} {g2} |" + "".join(chr(b) if 32 <= b < 127 else "." for b in chunk) + "|\n")
        prev = chunk
        off += len(chunk)
    if data:
        out.append(f"{len(data):08x}\n")
    return "".join(out)


def run_prog_case(binary, cs, cwd):
    args = cs.get("args", [])
    stdin = cs.get("stdin", "")
    name = "./" + binary + " " + " ".join(a if a and " " not in a else repr(a) for a in args)

    def go(cmd):
        try:
            r = subprocess.run(cmd, cwd=cwd, input=stdin.encode(), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               timeout=TIMEOUT)
            return r.stdout.decode("utf-8", "replace"), r.stderr.decode("utf-8", "replace"), r.returncode
        except subprocess.TimeoutExpired:
            return None, None, "TIMEOUT"

    got_o, got_e, code = go(["./" + binary, *args])
    if code == "TIMEOUT":
        return {"name": name, "ok": False, "exp": L("จบภายในเวลา", "finish in time"), "got": L("ค้าง (อาจรออ่าน stdin)", "hangs (maybe waiting for stdin)")}
    if isinstance(code, int) and code < 0:
        return {"name": name, "ok": False, "exp": L("ทำงานจนจบ", "run to the end"), "got": L(f"พัง (signal {-code})", f"crash (signal {-code})")}
    ref = cs.get("ref")
    if ref == "hexdump_C":
        data = b""
        for a in args[1:]:
            p = os.path.join(cwd, a)
            if os.path.isfile(p) and os.access(p, os.R_OK):
                data += open(p, "rb").read()
        if len(args) <= 1:
            data = stdin.encode()
        exp_o, exp_e = hexdump_C(data), None
    elif ref:
        exp_o, exp_e, _ = go([ref, *args])
        exp_e = exp_e.replace(ref + ":", "PROG:")
    else:
        exp_o, exp_e = cs.get("stdout", ""), cs.get("stderr")
    got_e_n = (got_e or "").replace("./" + binary + ":", "PROG:").replace(binary + ":", "PROG:")
    ok = got_o == exp_o
    check_err = cs.get("check_stderr", exp_e is not None)
    if check_err and exp_e is not None:
        ok = ok and got_e_n == exp_e
    res = {"name": name, "ok": ok}
    if not ok:
        def show(o, e):
            t = (o or "").replace("\n", "$\n")
            if check_err and e:
                t += "\n[stderr] " + e.replace("PROG:", binary + ":").replace("\n", "$\n")
            return t[:1500] or L("(ว่าง)", "(empty)")
        res["exp"] = show(exp_o, exp_e)
        res["got"] = show(got_o, got_e_n)
    return res


# ───────────────────────── one exercise ─────────────────────────
# ───────────────────────── git / files ─────────────────────────
def git_info(root):
    """ข้อมูล git ของโฟลเดอร์งาน: ไฟล์ที่ commit แล้ว / แก้ค้าง / commit ที่ยังไม่ push  (None ถ้าไม่ใช่ git)"""
    code, _ = run(["git", "-C", root, "rev-parse", "--show-toplevel"])
    if code != 0:
        return None
    # -z: ชื่อไฟล์แปลก ๆ (เช่น Shell01 ex05) ไม่ถูก git ใส่เครื่องหมายคำพูด
    code, out = run(["git", "-C", root, "ls-tree", "-r", "-z", "--name-only", "HEAD"])
    committed = set(out.split("\0")) - {""} if code == 0 else set()
    _, out = run(["git", "-C", root, "diff", "-z", "--name-only", "--relative", "HEAD"])
    modified = set(out.split("\0")) - {""} if code == 0 else set()
    code, out = run(["git", "-C", root, "rev-list", "--count", "@{u}..HEAD"])
    ahead = int(out.strip()) if code == 0 and out.strip().isdigit() else None
    code, out = run(["git", "-C", root, "rev-parse", "--abbrev-ref", "@{u}"])
    upstream = out.strip() if code == 0 else None
    return {"committed": committed, "modified": modified, "ahead": ahead, "upstream": upstream}


def extra_type(name, full):
    if os.path.isdir(full):
        return "dir"
    if name.endswith((".o", ".a", ".gch", ".so", ".out")) or name in ("a.out",):
        return "build"
    if name.endswith((".swp", ".swo", "~", ".bak", ".orig", ".tmp")):
        return "temp"
    if name.startswith("."):
        return "hidden"
    return "other"


def rm_command(rel, extras):
    """คำสั่งลบไฟล์เกินออกจาก git (รวม *.o ถ้ามีหลายไฟล์)"""
    parts, exts = [], {}
    for e in extras:
        ext = os.path.splitext(e["name"])[1]
        if e["type"] == "build" and ext:
            exts.setdefault(ext, []).append(e["name"])
    for e in extras:
        ext = os.path.splitext(e["name"])[1]
        if e["type"] == "build" and ext and len(exts.get(ext, [])) > 1:
            g = f"'{rel}/*{ext}'"
            if g not in parts:
                parts.append(g)
        else:
            parts.append(f"{rel}/{e['name']}" + ("/" if e["type"] == "dir" else ""))
    return f"git rm -r {' '.join(parts)} && git commit -m \"remove extra files\" && git push"


class Grader:
    def __init__(self, proj, root, mine=False):
        self.proj = proj
        self.root = root
        self.mine = mine
        self.tests = os.path.join(TESTS, proj)
        self.work = tempfile.mkdtemp(prefix="grader_")
        self.has_norm = have("norminette")
        self.git = git_info(root)

    def _git_state(self, rel, fn):
        """ok | modified (แก้แล้วยังไม่ commit) | not_pushed (ยังไม่ commit เลย) | local (ไม่มี git)"""
        g = self.git
        if not g:
            return "local"
        path = f"{rel}/{fn}"
        if path not in g["committed"]:
            return "not_pushed"
        if path in g["modified"]:
            return "modified"
        return "ok"

    def _extra_info(self, exdir, name, pushed):
        full = os.path.join(exdir, name)
        info = {"name": name, "type": extra_type(name, full)}
        if info["type"] == "dir":
            if pushed is not None:
                kids = [k.split("/", 1)[1] for k in pushed.get(name, []) if "/" in k]
            else:
                kids = [os.path.relpath(os.path.join(dp, f), full) for dp, _, fs in os.walk(full) for f in fs]
            info["n"] = len(kids)
            info["children"] = sorted(kids)[:8]
        return info

    def cleanup(self):
        shutil.rmtree(self.work, ignore_errors=True)

    # ---- compile & test with given sources {fname: text} ----
    def build_and_test(self, spec, srcs, exdir):
        """คอมไพล์และรันเทสต์ คืน (status, compile_out, test_out, cases)"""
        wd = tempfile.mkdtemp(dir=self.work)
        for fn, txt in srcs.items():
            with open(os.path.join(wd, fn), "w", encoding="utf-8") as f:
                f.write(txt)
        for extra in os.listdir(exdir) if exdir and os.path.isdir(exdir) else []:
            if extra.endswith(".h") and extra not in srcs:
                shutil.copy(os.path.join(exdir, extra), wd)
        inc = ["-I", wd, "-I", os.path.join(self.tests, "include"), "-I", LIB]
        t = spec["type"]
        if t == "func":
            objs = []
            cc_out = ""
            for fn in [f for f in spec["files"] if f.endswith(".c")]:
                o = os.path.join(wd, fn + ".o")
                code, out = run(["cc", *CFLAGS, *inc, "-c", os.path.join(wd, fn), "-o", o])
                cc_out += out
                if code != 0:
                    return "COMPILE", cc_out, "", []
                o2 = os.path.join(wd, fn + ".t.o")
                run(["cc", "-w", "-Dmain=peer_main_not_allowed", *inc, "-c", os.path.join(wd, fn), "-o", o2])
                objs.append(o2)
            exe = os.path.join(wd, "t")
            code, out = run(["cc", "-w", *inc, os.path.join(self.tests, spec["ex"] + ".c"), *objs, "-o", exe])
            if code != 0:
                return "LINK", out, "", []
            return self._run_test([exe], cc_out)
        if t == "header":
            exe = os.path.join(wd, "t")
            code, out = run(["cc", *CFLAGS, "-Wno-unused-function", *inc,
                             os.path.join(self.tests, spec["ex"] + ".c"), "-o", exe])
            if code != 0:
                return "COMPILE", out, "", []
            return self._run_test([exe], "")
        if t == "prog":
            fn = spec["files"][0]
            pdir, rdir = os.path.join(wd, "p"), os.path.join(wd, "r")
            os.makedirs(pdir)
            os.makedirs(rdir)
            code, out = run(["cc", *CFLAGS, os.path.join(wd, fn), "-o", os.path.join(pdir, "a.out")])
            if code != 0:
                return "COMPILE", out, "", []
            run(["cc", "-w", os.path.join(self.tests, "ref_" + spec["ex"] + ".c"), "-o", os.path.join(rdir, "a.out")])
            cases = []
            for line in read(os.path.join(self.tests, "args.txt")).split("\n"):
                import shlex
                args = shlex.split(line)
                _, exp = run(["./a.out", *args], cwd=rdir, timeout=TIMEOUT)
                code, got = run(["./a.out", *args], cwd=pdir, timeout=TIMEOUT)
                name = "./a.out " + line
                ok = code not in ("TIMEOUT",) and got == exp
                cs = {"name": name, "ok": ok}
                if not ok:
                    cs["exp"] = "$\n".join(exp.split("\n"))
                    cs["got"] = L("พัง/ค้าง", "Crash/Hang") if code == "TIMEOUT" or (isinstance(code, int) and code < 0) else "$\n".join(got.split("\n"))
                cases.append(cs)
            return ("OK" if all(cs["ok"] for cs in cases) else "KO"), "", "", cases
        if t == "script":
            sd = os.path.join(wd, "s")
            os.makedirs(sd)
            for fn in spec["files"]:
                shutil.copy(os.path.join(wd, fn), sd)
            for fn in spec["files"]:
                if fn.endswith(".c"):
                    code, out = run(["cc", *CFLAGS, "-c", os.path.join(sd, fn), "-o", os.path.join(wd, fn + ".o")])
                    if code != 0:
                        return "COMPILE", out, "", []
            code, out = run(["sh", "libft_creator.sh"], cwd=sd, timeout=TIMEOUT)
            cases = [{"name": L("sh libft_creator.sh สร้าง libft.a", "sh libft_creator.sh creates libft.a"), "ok": os.path.isfile(os.path.join(sd, "libft.a"))}]
            if not cases[0]["ok"]:
                cases[0].update(exp=L("มีไฟล์ libft.a", "libft.a exists"), got=out.strip() or L("ไม่มีไฟล์", "Missing file"))
                return "KO", "", "", cases
            exe = os.path.join(wd, "t")
            code, out = run(["cc", "-w", "-I", LIB, os.path.join(self.tests, "ex00.c"), "-L", sd, "-lft", "-o", exe])
            if code != 0:
                cases.append({"name": L("ลิงก์กับ libft.a", "link with libft.a"), "ok": False, "exp": L("ฟังก์ชันครบ 5 ตัว", "all 5 functions"), "got": out[-300:]})
                return "KO", "", "", cases
            st, a, b, more = self._run_test([exe], "")
            return st, a, b, cases + more
        if t == "make":
            return self._run_make(wd, srcs)
        if t == "make_prog":
            return self._run_make_prog(spec, wd)
        if t == "shell":
            import importlib.util
            sp = importlib.util.spec_from_file_location("check_" + self.proj, os.path.join(self.tests, "check.py"))
            mod = importlib.util.module_from_spec(sp)
            sp.loader.exec_module(mod)
            try:
                cases = mod.check(spec["ex"], exdir, wd)
            except Exception as e:  # noqa: BLE001
                cases = [{"name": L("ตรวจไม่สำเร็จ", "Check failed"), "ok": False, "exp": L("ไม่มี error", "no error"), "got": f"{type(e).__name__}: {e}"}]
            return ("OK" if cases and all(c["ok"] for c in cases) else "KO"), "", "", cases
        return "KO", "", "", []

    def _run_test(self, cmd, cc_out):
        code, out = run(cmd, timeout=TIMEOUT)
        cases = parse_cases(out)
        if code == "TIMEOUT":
            return "TIMEOUT", cc_out, out, cases
        if code == 0:
            return "OK", cc_out, out, cases
        if code == 1:
            return "KO", cc_out, out, cases
        return "CRASH", cc_out, out, cases

    def _prog_spec(self, ex):
        try:
            return json.load(open(os.path.join(self.tests, f"prog_{ex}.json"), encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def _run_make_prog(self, spec, wd):
        prog = self._prog_spec(spec["ex"])
        binary = prog.get("binary", "a.out")
        code, out = run(["make"], cwd=wd, timeout=120)
        bpath = os.path.join(wd, binary)
        if code != 0 or not os.path.isfile(bpath):
            return "COMPILE", out, "", []
        cases = []
        flags_ok = all(f in out for f in ("-Wall", "-Wextra", "-Werror"))
        cases.append({"name": L("make คอมไพล์ด้วย -Wall -Wextra -Werror", "make compiles with -Wall -Wextra -Werror"), "ok": flags_ok,
                      "exp": L("เห็น flag ครบ", "all flags shown"), "got": out.strip()[-300:]})
        rd = os.path.join(wd, "_run")
        os.makedirs(rd)
        make_fixtures(rd)
        shutil.copy(bpath, os.path.join(rd, binary))
        for cs in prog.get("cases", []):
            cases.append(run_prog_case(binary, cs, rd))
        mf = read(os.path.join(wd, "Makefile"))
        for rule in prog.get("rules", []):
            has = re.search(r"^" + re.escape(rule) + r"\s*:", mf, re.M) is not None
            cases.append({"name": L(f"Makefile มี rule '{rule}'", f"Makefile has rule '{rule}'"), "ok": has, "exp": L("มี", "yes"), "got": L("ไม่มี", "no")})
        run(["make", "clean"], cwd=wd, timeout=60)
        left = [f for f in os.listdir(wd) if f.endswith(".o")]
        cases.append({"name": L("make clean ลบไฟล์ .o", "make clean removes .o files"), "ok": not left, "exp": L("ไม่เหลือ .o", "no .o left"), "got": " ".join(left)})
        run(["make", "fclean"], cwd=wd, timeout=60)
        cases.append({"name": L(f"make fclean ลบ {binary}", f"make fclean removes {binary}"), "ok": not os.path.exists(bpath), "exp": L("ไม่มีไฟล์", "Missing file"), "got": L("ยังอยู่", "still there")})
        for cs in cases:
            if cs["ok"]:
                cs.pop("exp", None)
                cs.pop("got", None)
        return ("OK" if all(c["ok"] for c in cases) else "KO"), "", "", cases

    def _run_make(self, wd, srcs):
        m = os.path.join(wd, "m")
        shutil.copytree(os.path.join(self.tests, "libft_srcs"), m)
        with open(os.path.join(m, "Makefile"), "w") as f:
            f.write(srcs.get("Makefile", ""))
        cases = []

        def chk(name, ok, exp="", got=""):
            cs = {"name": name, "ok": bool(ok)}
            if not ok:
                cs.update(exp=exp, got=got)
            cases.append(cs)

        mk = lambda *a: run(["make", *a], cwd=m, timeout=TIMEOUT)[1]
        o1 = mk()
        lib = os.path.join(m, "libft.a")
        chk(L("make สร้าง libft.a", "make creates libft.a"), os.path.isfile(lib), L("มี libft.a", "libft.a exists"), o1[-300:])
        chk(L("make แสดงคำสั่ง cc พร้อม -Wall -Wextra -Werror", "make shows cc commands with -Wall -Wextra -Werror"),
            all(x in o1 for x in ("-Wall", "-Wextra", "-Werror")), L("เห็น flag ครบ", "all flags shown"), o1[-300:])
        chk(L(".o อยู่ข้าง .c ใน srcs/", ".o files next to .c in srcs/"), os.path.isfile(os.path.join(m, "srcs", "ft_putchar.o")))
        _, nm = run(["nm", lib])
        n = len(set(re.findall(r" T _?(ft_putchar|ft_swap|ft_putstr|ft_strlen|ft_strcmp)$", nm, re.M)))
        chk(L("libft.a มีครบ 5 ฟังก์ชัน", "libft.a has all 5 functions"), n == 5, "5", str(n))
        o2 = mk()
        chk(L("รัน make ซ้ำ ไม่คอมไพล์ใหม่", "running make again does not recompile"), not re.search(r"(^|\s)(cc|gcc|ar)\s", o2), L("ไม่มีคำสั่ง cc/ar", "no cc/ar command"), o2[-200:])
        mk("clean")
        chk(L("make clean ลบ .o แต่ libft.a ยังอยู่", "make clean removes .o but keeps libft.a"),
            not any(f.endswith(".o") for f in os.listdir(os.path.join(m, "srcs"))) and os.path.isfile(lib))
        mk("fclean")
        chk(L("make fclean ลบ libft.a", "make fclean removes libft.a"), not os.path.isfile(lib))
        mk("re")
        chk(L("make re สร้างใหม่ได้", "make re rebuilds"), os.path.isfile(lib))
        return ("OK" if all(c["ok"] for c in cases) else "KO"), "", "", cases

    # ---- main entry per exercise ----
    def grade_ex(self, spec, override=None):
        ex = spec["ex"]
        res = {"ex": ex, "files": spec["files"], "issues": [], "cases": [], "sources": {}, "fixed": {},
               "solution": {}, "hints": [], "renames": [], "deletes": [], "status": "OK", "after_fix": None}
        exdir = os.path.join(self.root, ex)
        top = [d for d in os.listdir(self.root) if os.path.isdir(os.path.join(self.root, d))]
        if not os.path.isdir(exdir):
            near = close_match(ex, [d for d in top if d not in [e["ex"] for e in PROJECTS[self.proj]]], 0.6)
            if near:
                res["issues"].append(issue("file", L(f"ชื่อโฟลเดอร์ผิด: {near} → ควรเป็น {ex}", f"Wrong folder name: {near} → should be {ex}"), why=char_diff(near, ex),
                                           fixable=True, code="folder_name"))
                res["renames"].append((near, ex))
                exdir = os.path.join(self.root, near)
            else:
                res["issues"].append(issue("file", L(f"ไม่มีโฟลเดอร์ {ex}", f"Folder {ex} is missing"), hint=L("ยังไม่ได้ทำ หรือยังไม่ได้ push ข้อนี้", "Not done yet, or not pushed"), code="folder_missing"))
                res["status"] = L("ไม่มีไฟล์", "Missing file")
                self._solution(res, spec)
                return res
        rel = os.path.relpath(exdir, self.root)
        local = sorted(os.listdir(exdir))
        git = self.git
        if git:
            pushed = {}                       # ชื่อในโฟลเดอร์ข้อ → [ไฟล์ข้างใน] (เฉพาะที่ commit แล้ว)
            for path in git["committed"]:
                if path.startswith(rel + "/"):
                    sub = path[len(rel) + 1:]
                    pushed.setdefault(sub.split("/")[0], []).append(sub)
            present = sorted(set(pushed) | set(local))
        else:
            pushed = None
            present = local
        is_pushed = lambda name: pushed is None or name in pushed
        fc = {"git": bool(git), "dir": rel, "required": [], "extra": [], "local": [], "cmd": ""}
        res["filecheck"] = fc
        srcs = {}
        used = set()
        if spec["files"] == ["*"]:
            prog = self._prog_spec(ex)
            for p in present:
                full = os.path.join(exdir, p)
                junk = p in ("a.out", ".DS_Store", prog.get("binary")) or p.endswith((".o", ".swp", "~")) or p.startswith(".")
                if os.path.isfile(full) and not junk:
                    srcs[p] = read(full)
                elif junk and not is_pushed(p):
                    fc["local"].append(p)
                elif junk:
                    res["issues"].append(issue("file", L(f"มีไฟล์เกินใน {ex}: {p}", f"Extra file in {ex}: {p}"), hint=L("ลบไฟล์ที่ได้จากการคอมไพล์ก่อน push", "Remove build products before pushing"),
                                               fixable=True, code="extra"))
                    fc["extra"].append(self._extra_info(exdir, p, pushed))
                    res["deletes"].append(f"{os.path.basename(exdir)}/{p}")
            if "Makefile" not in srcs:
                res["issues"].append(issue("file", L("ไม่มี Makefile", "Makefile is missing"), hint=L("ข้อนี้ต้องส่ง Makefile ที่มี rule all clean fclean", "This exercise needs a Makefile with rules all clean fclean"), code="missing"))
                res["status"] = L("ไม่มีไฟล์", "Missing file")
                res["sources"] = srcs
                return res
            spec = dict(spec, files=sorted(srcs))
            res["files"] = spec["files"]
        wild = PROJ_SPEC_WILD(spec, self.proj)
        for fn in spec["files"]:
            if fn in srcs:
                used.add(fn)
                fc["required"].append({"name": fn, "state": self._git_state(rel, fn)})
                continue
            if fn in present and os.path.isfile(os.path.join(exdir, fn)):
                srcs[fn] = read(os.path.join(exdir, fn))
                used.add(fn)
                st = self._git_state(rel, fn)
                fc["required"].append({"name": fn, "state": st})
                if st == "not_pushed":
                    res["issues"].append(issue("file", L(f"{fn} ยังไม่ได้ push (Moulinette มองไม่เห็นไฟล์นี้)", f"{fn} is not pushed (Moulinette cannot see it)"),
                                               hint=L(f"git add {rel}/{fn} → git commit → git push", f"git add {rel}/{fn} → git commit → git push"),
                                               file=fn, code="not_pushed"))
                continue
            near = close_match(fn, [p for p in present if p not in spec["files"]])
            if near:
                res["issues"].append(issue("file", L(f"ชื่อไฟล์ผิด: {near} → ควรเป็น {fn}", f"Wrong file name: {near} → should be {fn}"), why=char_diff(near, fn),
                                           hint=L("Moulinette หาไฟล์จากชื่อเป๊ะ ๆ ถ้าชื่อผิดจะได้ 0 ทั้งข้อ", "Moulinette looks for the exact name; a wrong name gives 0 for the exercise"),
                                           file=near, fixable=True, code="wrong_name"))
                res["renames"].append((f"{os.path.basename(exdir)}/{near}", f"{ex}/{fn}"))
                srcs[fn] = read(os.path.join(exdir, near))
                used.add(near)
                fc["required"].append({"name": fn, "state": "renamed", "from": near})
            else:
                res["issues"].append(issue("file", L(f"ไม่มีไฟล์ {fn}", f"Missing file {fn}"), hint=L("ยังไม่ได้ทำ หรือยังไม่ได้ push ข้อนี้", "Not done yet, or not pushed"),
                                           code="missing"))
                fc["required"].append({"name": fn, "state": "missing"})
        for p in present:
            if wild:
                break
            if p in used:
                continue
            if not is_pushed(p):
                fc["local"].append(p)         # อยู่ในเครื่องเฉยๆ ไม่ได้ push → ไม่นับ
                continue
            info = self._extra_info(exdir, p, pushed)
            fc["extra"].append(info)
            is_junk = info["type"] in ("build", "temp") or p in (".DS_Store",)
            res["issues"].append(issue("file", L(f"มีไฟล์เกินใน {ex}: {p}", f"Extra file in {ex}: {p}"),
                                       hint=L("โจทย์ห้ามมีไฟล์อื่น ลบออกด้วย git rm ก่อน push", "No other files allowed; remove it with git rm before pushing"),
                                       fixable=is_junk and self.mine, code="extra"))
            if is_junk:
                res["deletes"].append(f"{os.path.basename(exdir)}/{p}")
        if fc["extra"]:
            fc["cmd"] = rm_command(rel, fc["extra"])
        for fn, txt in (override or {}).items():
            if fn in srcs or fn in spec["files"]:
                srcs[fn] = txt
        res["sources"] = dict(srcs)
        if len(srcs) < len(spec["files"]):
            res["status"] = L("ไม่มีไฟล์", "Missing file")
            self._solution(res, spec)
            return res

        # header / main / forbidden  (แก้คอมไพล์ก่อน เพราะเลขบรรทัดอ้างอิงไฟล์เดิม)
        fixed = {fn: (self._fix_compile(fn, t, exdir) if fn.endswith(".c") else t) for fn, t in srcs.items()}
        for fn, txt in srcs.items():
            if spec["type"] == "shell":
                continue
            if not has_header(txt):
                if needs_header(fn):
                    res["issues"].append(issue("rule", L("ไม่มี 42 header", "Missing 42 header"), hint=L("vim: พิมพ์ :Stdheader", "vim: type :Stdheader"), file=fn, line=1,
                                               fixable=True, code="header"))
                    fixed[fn] = fix_header(fixed[fn], fn)
                elif spec["type"] in ("script", "make"):
                    res["issues"].append(issue("tip", L(f"{fn} ไม่มี 42 header (ไม่ผิด)", f"{fn} has no 42 header (that's fine)"),
                                               hint=L("Norm บังคับ header แค่ไฟล์ .c/.h · ถ้าจะใส่ในไฟล์ .sh ต้องอยู่ใต้บรรทัด #!/bin/sh",
                                                      "The Norm only requires the header in .c/.h files · in a .sh file it must go below #!/bin/sh"),
                                               file=fn, code="header_optional"))
            if fn.endswith(".c") and spec["type"] not in ("prog", "make_prog") and main_line(txt):
                res["issues"].append(issue("rule", L("มีฟังก์ชัน main ในไฟล์ (ห้ามมี)", "File contains a main function (not allowed)"),
                                           hint=L("ลบ main ออก ใช้ main ทดสอบในไฟล์อื่นที่ไม่ได้ push", "Remove main; test with a separate file you do not push"),
                                           file=fn, line=main_line(txt), fixable=True, code="main"))
                fixed[fn] = fix_remove_main(fixed[fn])

        # norminette
        norm_issues = self._norm(srcs, exdir)
        if any(i.get("code") == "header" for i in res["issues"]):
            norm_issues = [i for i in norm_issues if not i["why"].startswith("INVALID_HEADER")]
        res["issues"] += norm_issues
        if any(i["fixable"] for i in norm_issues):
            for fn in fixed:
                if fn.endswith(".c"):
                    fixed[fn] = fix_norm_text(fixed[fn])

        # compile + forbidden + tests
        status, cc_out, _test_out, cases = self.build_and_test(spec, srcs, exdir)
        if status in ("COMPILE", "LINK"):
            for fn in srcs:
                iss, fixes = parse_cc(cc_out, fn)
                for i2 in iss:
                    if i2["file"] != fn and i2["file"] and not cc_out.count(fn):
                        continue
                res["issues"] += iss
            if not any(i["kind"] == "compile" for i in res["issues"]):
                res["issues"].append(issue("compile", L("คอมไพล์ไม่ผ่าน", "Does not compile") if status == "COMPILE" else
                                           L("ชื่อฟังก์ชันหรือ prototype ไม่ตรงโจทย์", "Function name or prototype does not match the subject"), why=cc_out.strip()[-600:],
                                           code="compile" if status == "COMPILE" else "link"))
            res["status"] = L("คอมไพล์ไม่ผ่าน", "Does not compile") if status == "COMPILE" else L("ใช้กับตัวเทสต์ไม่ได้", "Cannot be used by the tests")
        else:
            res["issues"] += self._forbidden(spec, srcs)
            for cs in cases:
                cs["name"] = en_case(cs["name"])
                for k in ("exp", "got"):
                    if k in cs:
                        cs[k] = en_case(cs[k]) if LANG == "en" and not re.search(r"[A-Za-z0-9$]", re.sub("[\u0e00-\u0e7f ]", "", cs[k])) else cs[k]
            res["cases"] = cases
            if status == "TIMEOUT":
                res["issues"].append(issue("crash", L(f"ค้างเกิน {TIMEOUT} วินาที", f"Hangs longer than {TIMEOUT} s"), hint=L("วนไม่จบ", "infinite loop"), code="timeout"))
            elif status == "CRASH":
                res["issues"].append(issue("crash", L("โปรแกรมพัง (crash/segfault)", "Program crashed (crash/segfault)"), code="crash"))
            for cs in cases:
                if not cs["ok"]:
                    res["issues"].append(issue("logic", L(cs["name"], strip_thai(cs["name"])), why=L(f"ควรได้: {cs.get('exp', '')}\nได้จริง: {cs.get('got', '')}", f"Expected: {cs.get('exp', '')}\nGot: {cs.get('got', '')}"),
                                               code="case"))
            if status != "OK":
                res["status"] = {"KO": L("ผลลัพธ์ผิด", "Wrong output"), "TIMEOUT": L("ค้าง", "Hangs"), "CRASH": L("พัง", "Crashes")}.get(status, status)
            if status != "OK":
                res["hints"] = guess_hints(self.proj, ex, cases, status)
        if res["status"] == "OK" and any(i["kind"] in FAIL_KINDS for i in res["issues"]):
            fails = [i for i in res["issues"] if i["kind"] in FAIL_KINDS]
            if all(i.get("code") == "not_pushed" for i in fails):
                res["status"] = L("ยังไม่ได้ push", "Not pushed")
            elif all(i["kind"] == "file" for i in fails):
                res["status"] = L("ไฟล์เกิน/ไฟล์ผิด", "Extra or wrong files")
            else:
                res["status"] = L("ผิดกฎ/Norm", "Rule/Norm error")
        if res["status"] == "OK" and res["renames"]:
            res["status"] = L("ชื่อไฟล์ผิด", "Wrong file name")

        # ตรวจเวอร์ชันที่แก้แล้วว่าผ่านไหม
        if fixed != srcs or res["renames"]:
            res["fixed"] = fixed
            res["after_fix"] = self._verify_fixed(spec, fixed, exdir)
        self._solution(res, spec)
        return res

    def _fix_compile(self, fn, text, exdir):
        """คอมไพล์ → แก้ error ที่แก้ได้ → คอมไพล์ใหม่ วนสูงสุด 5 รอบ"""
        wd = tempfile.mkdtemp(dir=self.work)
        inc = ["-I", wd, "-I", os.path.join(self.tests, "include")]
        if exdir and os.path.isdir(exdir):
            inc += ["-I", exdir]
        for _ in range(5):
            p = os.path.join(wd, fn)
            with open(p, "w", encoding="utf-8") as f:
                f.write(text)
            code, out = run(["cc", *CFLAGS, *DIAG, *inc, "-c", p, "-o", p + ".o"])
            if code == 0:
                break
            _, fixes = parse_cc(out, fn)
            new = apply_cc_fixes(text, fixes) if fixes else text
            if new == text:
                break
            text = new
        return text

    def _norm(self, srcs, exdir):
        if not self.has_norm:
            return []
        wd = tempfile.mkdtemp(dir=self.work)
        files = []
        for fn, txt in srcs.items():
            if fn.endswith((".c", ".h")):
                p = os.path.join(wd, fn)
                with open(p, "w", encoding="utf-8") as f:
                    f.write(txt)
                files.append(p)
        if not files:
            return []
        flag = "CheckDefine" if self.proj == "C08" else "CheckForbiddenSourceHeader"
        _, out = run(["norminette", "-R", flag, *files], cwd=wd)
        issues, seen = [], set()
        for block in re.split(r"\n(?=\S+: (?:Error|OK))", out):
            m = re.match(r"(\S+): Error", block)
            if m:
                for i in parse_norm(block, os.path.basename(m.group(1))):
                    key = (i["file"], i["line"], i["title"])
                    if key not in seen:
                        seen.add(key)
                        issues.append(i)
        issues.sort(key=lambda i: (i["file"] or "", i["line"] or 0))
        return issues

    def _norm_ok(self, srcs):
        return not [i for i in self._norm(srcs, None)]

    def _forbidden(self, spec, srcs):
        allowed = {a.lstrip("_") for a in spec["allowed"]}
        if "basename" in allowed:
            allowed.add("xpg_basename")
        objs = []
        wd = tempfile.mkdtemp(dir=self.work)
        for fn, txt in srcs.items():
            if fn.endswith(".c"):
                p = os.path.join(wd, fn)
                with open(p, "w", encoding="utf-8") as f:
                    f.write(txt)
                o = p + ".o"
                code, _ = run(["cc", "-w", "-I", os.path.join(self.tests, "include"), "-c", p, "-o", o])
                if code == 0:
                    objs.append(o)
        if not objs:
            return []
        _, nm = run(["nm", *objs])
        defined, undef = set(), set()
        for l in nm.split("\n"):
            parts = l.split()
            if len(parts) >= 2:
                name = parts[-1].lstrip("_")
                (undef if parts[-2] == "U" else defined).add(name)
        if spec["type"] == "prog":
            allowed |= {"main"}
        allsrc = "\n".join(srcs.values())
        issues = []
        for s in sorted(undef - defined - allowed):
            if s in ("stack_chk_fail", "stack_chk_guard", "dyld_stub_binder", ""):
                continue
            if s in ("memset", "memcpy", "memmove", "bzero") or s.endswith("_chk"):
                if not re.search(r"\b" + s + r"\s*\(", allsrc):
                    continue
            shown = s
            ln = None
            for fn, txt in srcs.items():
                for i, l in enumerate(txt.split("\n")):
                    look = "printf" if s in ("puts", "putchar") else s
                    if re.search(r"\b" + look + r"\s*\(", l):
                        ln, shown = (i + 1, fn), look
                        break
                if ln:
                    break
            issues.append(issue("rule", L(f"ใช้ฟังก์ชันต้องห้าม: {shown}", f"Forbidden function used: {shown}"),
                                hint=L(f"ข้อนี้อนุญาตแค่: {', '.join(spec['allowed']) or 'ไม่มีเลย'}", f"Allowed here: {', '.join(spec['allowed']) or 'nothing'}"),
                                file=ln[1] if ln else None, line=ln[0] if ln else None, code="forbidden"))
        return issues

    def _verify_fixed(self, spec, fixed, exdir):
        out = {}
        norm = self._norm(fixed, exdir) if self.has_norm else []
        out["norm"] = len(norm) == 0 if self.has_norm else None
        out["norm_left"] = [L(f"บรรทัด {i['line']}: {i['title']}", f"line {i['line']}: {i['title']}") for i in norm][:6]
        status, cc_out, _, cases = self.build_and_test(spec, fixed, exdir)
        out["compile"] = status not in ("COMPILE", "LINK")
        out["tests"] = status == "OK"
        out["status"] = status
        return out

    def _solution(self, res, spec):
        d = os.path.join(self.tests, "solutions", spec["ex"])
        if os.path.isdir(d):
            for fn in spec["files"]:
                p = os.path.join(d, fn)
                if os.path.isfile(p):
                    res["solution"][fn] = read(p)


# ───────────────────────── terminal UI ─────────────────────────
VERSION = "3.1"


def dwidth(s):
    """ความกว้างที่แสดงจริงบนจอ (สระ/วรรณยุกต์ไทยกว้าง 0, emoji กว้าง 2)"""
    import unicodedata
    s = re.sub(r"\x1b\[[0-9;]*m", "", s)
    w = 0
    for ch in s:
        if unicodedata.combining(ch) or unicodedata.category(ch) in ("Mn", "Me", "Cf"):
            continue
        if ch in "ัิีึืฺุู็่้๊๋์ํ๎":
            continue
        w += 2 if unicodedata.east_asian_width(ch) in ("W", "F") or ord(ch) >= 0x1F300 else 1
    return w


def pad(s, n):
    return s + " " * max(0, n - dwidth(s))


def cut(s, n):
    if dwidth(s) <= n:
        return s
    out = ""
    for ch in s:
        if dwidth(out + ch + "…") > n:
            break
        out += ch
    return out + "…"


def term_width():
    return max(60, min(110, shutil.get_terminal_size((100, 30)).columns))


def box(lines, color="36"):
    w = max(dwidth(l) for l in lines) + 4
    w = min(max(w, 48), term_width() - 4)
    print("  " + c(color, "╭" + "─" * (w - 2) + "╮"))
    for l in lines:
        print("  " + c(color, "│") + " " + pad(cut(l, w - 4), w - 4) + " " + c(color, "│"))
    print("  " + c(color, "╰" + "─" * (w - 2) + "╯"))


def banner():
    login = os.environ.get("USER", "student")
    lang = "ไทย" if LANG == "th" else "English"
    print()
    box([c("1;36", "◆ PISCINE GRADER") + dim(f"   v{VERSION} · 42 Bangkok"),
         dim(f"{login} · {datetime.datetime.now():%d/%m/%Y %H:%M} · {L('ภาษา', 'lang')}: {lang}")])


def kind_label(kind):
    icon, label = KIND[kind]
    return f"{icon} {pad(label, 9)}"


def print_table(results):
    w = term_width()
    fw = max(16, w - 46)
    head = f"  {pad(L('ข้อ', 'Ex'), 6)}{pad(L('ไฟล์', 'Files'), fw)}{pad(L('เคส', 'Cases'), 9)}{L('ผล', 'Result')}"
    print(dim(head))
    print(dim("  " + "─" * (w - 4)))
    for r in results:
        ok = r["status"] == "OK"
        n_ok = sum(1 for x in r["cases"] if x["ok"])
        cnt = f"{n_ok}/{len(r['cases'])}" if r["cases"] else "—"
        tag = green("✔ " + L("ผ่าน", "OK")) if ok else red("✘ " + r["status"])
        files = cut(", ".join(r["files"]), fw - 2)
        print(f"  {pad(bold(r['ex']), 6)}{pad(dim(files) if ok else files, fw)}{pad(cnt, 9)}{tag}")


def print_details(r):
    fixn = sum(1 for i in r["issues"] if i.get("fixable"))
    head = f"  {red('✘')} {bold(r['ex'])} {dim('·')} {r['status']}"
    if fixn:
        head += dim(L(f"   ⚡ แก้อัตโนมัติได้ {fixn} จุด", f"   ⚡ {fixn} auto-fixable"))
    print(head)
    by_kind = {}
    for i in r["issues"]:
        by_kind.setdefault(i["kind"], []).append(i)
    for kind in ("file", "rule", "compile", "crash", "norm", "logic", "tip"):
        items = by_kind.get(kind, [])
        limit = 8 if kind == "norm" else 6
        for i in items[:limit]:
            where = (L(f"บรรทัด {i['line']}", f"line {i['line']}") + "  ") if i.get("line") else ""
            fx = c("33", " ⚡") if i.get("fixable") else ""
            title = dim(i["title"]) if kind == "tip" else i["title"]
            print(f"    {dim('│')} {kind_label(kind)} {dim(where)}{title}{fx}")
            if kind == "logic" and i.get("why"):
                for l in i["why"].split("\n")[:2]:
                    print(f"    {dim('│')}            {dim(cut(l, term_width() - 20))}")
            elif kind == "file" and i.get("why"):
                print(f"    {dim('│')}            {dim('→ ' + i['why'])}")
            elif i.get("hint") and kind in ("file", "compile", "rule"):
                print(f"    {dim('│')}            {dim('→ ' + i['hint'])}")
        if len(items) > limit:
            print(f"    {dim('│')}            " + dim(L(f"...และอีก {len(items) - limit} จุด", f"...and {len(items) - limit} more")))
    for h in r["hints"][:2]:
        print(f"    {dim('│')} 💡 {blue(h)}")
    print()


def print_tips(results):
    """ข้อที่ผ่านแต่มีข้อแนะนำ (เช่น Makefile ไม่มี header)"""
    for r in results:
        if r["status"] == "OK":
            for i in r["issues"]:
                if i["kind"] == "tip":
                    print(f"  {dim('💡 ' + r['ex'] + ' · ' + i['title'])}")


def print_git_warnings(gs):
    lines = []
    if gs["not_pushed"]:
        lines.append(red(L("⬆ ยังไม่ได้ push: ", "⬆ Not pushed: ")) + ", ".join(gs["not_pushed"]))
    if gs["modified"]:
        lines.append(yellow(L("✏️  แก้แล้วยังไม่ commit: ", "✏️  Edited, not committed: ")) + ", ".join(gs["modified"]))
    if gs["ahead"]:
        lines.append(yellow(L(f"⬆ มี {gs['ahead']} commit ที่ยังไม่ git push", f"⬆ {gs['ahead']} commit(s) not pushed yet")))
    if lines:
        lines.append(dim(L("Moulinette ตรวจเฉพาะที่ push แล้ว → git add · git commit · git push", "Moulinette only grades what is pushed → git add · git commit · git push")))
        print()
        box(lines, "33")


def progress(i, n, ex):
    if not TTY:
        return
    w = 24
    done = int(w * i / max(n, 1))
    bar = c("36", "█" * done) + dim("░" * (w - done))
    sys.stdout.write(f"\r\033[2K  {bar} {i}/{n}  {dim(L('กำลังตรวจ', 'checking'))} {ex}")
    sys.stdout.flush()


def summarize(results):
    passed = sum(1 for r in results if r["status"] == "OK")
    last = L("ไม่มี", "none")
    for r in results:
        if r["status"] != "OK":
            break
        last = r["ex"]
    return passed, last


def print_summary(results):
    passed, last = summarize(results)
    bar = "".join(green("■") if r["status"] == "OK" else red("■") for r in results)
    fixn = sum(1 for r in results for i in r["issues"] if i.get("fixable"))
    first = next((r["ex"] for r in results if r["status"] != "OK"), "—")
    lines = [f"{bar}  " + bold(f"{passed}/{len(results)}") + L(" ข้อผ่าน", " passed"),
             L(f"Moulinette ผ่านถึง {bold(last)}   ·   ข้อแรกที่พัง {bold(first)}",
               f"Moulinette reaches {bold(last)}   ·   first failure {bold(first)}")]
    if fixn:
        lines.append(c("33", L(f"⚡ แก้อัตโนมัติได้ {fixn} จุด", f"⚡ {fixn} problems can be fixed automatically")))
    print()
    box(lines, "32" if passed == len(results) else "33")
    print(dim("  " + L("ตัวตรวจช่วยดูผลเท่านั้น ตอน evaluate ยังต้องให้เพื่อนอธิบายโค้ดตามใบประเมิน",
                       "The grader only helps; during an evaluation your peer must still explain the code")))


# ───────────────────────── menu ─────────────────────────
def getkey():
    import termios
    import tty
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == "\x1b":
            ch += sys.stdin.read(2)
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def choose(title, options, default=0, hints=None):
    """เมนูเลือกด้วยลูกศร ↑↓ + Enter (ถ้าไม่ใช่ terminal ใช้พิมพ์ตัวเลขแทน)"""
    print("\n  " + bold(title))
    if not (sys.stdin.isatty() and TTY):
        for i, o in enumerate(options):
            print(f"    {i + 1}) {o}")
        try:
            k = int(input(L("  เลือกหมายเลข: ", "  Choose a number: ")).strip() or default + 1) - 1
        except (ValueError, EOFError):
            k = default
        return max(0, min(k, len(options) - 1))
    idx = default
    lines = len(options) + 1

    def draw(first=False):
        if not first:
            sys.stdout.write(f"\033[{lines}A")
        for i, o in enumerate(options):
            if i == idx:
                sys.stdout.write("\033[2K    " + c("36;1", "❯ ") + c("1", o) + "\n")
            else:
                sys.stdout.write("\033[2K      " + dim(o) + "\n")
        tip = (hints[idx] if hints and idx < len(hints) and hints[idx] else
               L("↑↓ เลือก · Enter ตกลง · q ออก", "↑↓ move · Enter select · q quit"))
        sys.stdout.write("\033[2K    " + dim(tip) + "\n")
        sys.stdout.flush()

    sys.stdout.write("\033[?25l")
    try:
        draw(True)
        while True:
            k = getkey()
            if k in ("\x1b[A", "k"):
                idx = (idx - 1) % len(options)
            elif k in ("\x1b[B", "j"):
                idx = (idx + 1) % len(options)
            elif k in ("\r", "\n"):
                return idx
            elif k in ("q", "\x03"):
                print()
                sys.exit(0)
            elif k.isdigit() and 0 < int(k) <= len(options):
                idx = int(k) - 1
            draw()
    finally:
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()


def ask(prompt, default=""):
    try:
        import glob
        import readline
        readline.set_completer_delims(" \t\n")
        readline.parse_and_bind("tab: complete")

        def comp(text, state):
            m = glob.glob(os.path.expanduser(text) + "*")
            m = [x + "/" if os.path.isdir(x) else x for x in m]
            return m[state] if state < len(m) else None

        readline.set_completer(comp)
    except ImportError:
        pass
    try:
        v = input("  " + c("36", "› ") + prompt + (dim(f" [{default}]") if default else "") + ": ").strip()
    except EOFError:
        v = ""
    return v or default


def find_my_work():
    """หาโฟลเดอร์ใน home ที่หน้าตาเหมือนงาน Piscine (มี exNN ข้างใน)"""
    home = os.path.expanduser("~")
    found = []
    for base in [home] + [os.path.join(home, d) for d in ("Desktop", "Documents", "piscine", "Piscine")]:
        try:
            names = os.listdir(base)
        except OSError:
            continue
        for d in names:
            p = os.path.join(base, d)
            if d.startswith(".") or not os.path.isdir(p) or d in ("grade_eval", "piscine-grader", "grade_backups"):
                continue
            try:
                subs = os.listdir(p)
            except OSError:
                continue
            if any(re.match(r"ex\d\d$", s) for s in subs):
                proj = detect_project(p)
                found.append((os.path.getmtime(p), p, proj[0] if proj else "?"))
    found.sort(reverse=True)
    return found[:12]


def clone(url, proj_hint="EVAL"):
    dest = os.path.join(os.path.expanduser("~"), "grade_eval",
                        f"{proj_hint}_{datetime.datetime.now().strftime('%m%d_%H%M%S')}")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    print(dim(L(f"  กำลัง clone ไปที่ {dest} ...", f"  Cloning into {dest} ...")))
    code, out = run(["git", "clone", "-q", url, dest], timeout=120)
    if code != 0:
        print(red(L("  clone ไม่สำเร็จ: ", "  Clone failed: ")) + out.strip()[-300:])
        print(dim(L("  เช็กลิงก์อีกที หรือเครื่องนี้ยังไม่ได้ตั้ง SSH key กับ intra",
                    "  Check the link, or this computer has no SSH key on the intranet yet")))
        sys.exit(1)
    return dest


def is_url(s):
    return bool(re.match(r"^(\S+@\S+:|https?://)", s)) or s.endswith(".git")


def settings():
    k = choose(L("ตั้งค่า", "Settings"), ["🇹🇭  ภาษาไทย", "🇬🇧  English", L("↩  กลับ", "↩  Back")],
               default=0 if LANG == "th" else 1)
    if k in (0, 1):
        save_config(lang="th" if k == 0 else "en")
        os.environ.pop("GRADER_LANG", None)
        os.execv(sys.executable, [sys.executable, os.path.abspath(__file__)])


def menu():
    banner()
    while True:
        opts = [L("🧑  ตรวจงานของฉัน", "🧑  Check my work"), L("👥  ตรวจงานเพื่อน", "👥  Check a peer's work"),
                L("📂  เลือกโฟลเดอร์เอง", "📂  Choose a folder"), L("⚙️   ตั้งค่า / ภาษา", "⚙️   Settings / language"),
                L("⟳   อัปเดตตัวตรวจ", "⟳   Update the grader"), L("✕   ออก", "✕   Quit")]
        tips = [L("หาโฟลเดอร์งานใน Home ให้ แก้โค้ดได้", "Finds your project folders; you can edit"),
                L("วางลิงก์ git จากหน้า eval แล้วจะ clone ให้", "Paste the git link from the eval page"),
                L("พิมพ์ path เอง (Tab ช่วยเติม)", "Type a path (Tab completes)"),
                L("เลือกภาษา ไทย/English", "Switch Thai/English"), L("git pull ตัวตรวจ", "git pull the grader"), ""]
        who = choose(L("จะทำอะไร?", "What do you want to do?"), opts, hints=tips)
        if who == 5:
            sys.exit(0)
        if who == 4:
            update()
            continue
        if who == 3:
            settings()
            continue
        break
    mine = who == 0
    if who == 0:
        works = find_my_work()
        opts = [f"{pad(os.path.basename(p), 26)} {pad(pr, 8)} {datetime.datetime.fromtimestamp(t):%d/%m %H:%M}"
                for t, p, pr in works] + [L("✎  พิมพ์ path เอง", "✎  Type a path")]
        k = choose(L("เลือกโฟลเดอร์งาน (เรียงจากที่แก้ล่าสุด)", "Choose your project folder (most recent first)"), opts)
        path = works[k][1] if k < len(works) else os.path.expanduser(
            ask(L("path ของโฟลเดอร์ (กด Tab ช่วยเติมได้)", "Folder path (Tab completes)")))
    elif who == 1:
        url = ask(L("วางลิงก์ git ของเพื่อน", "Paste your peer's git link"))
        path = clone(url) if is_url(url) else os.path.expanduser(url)
    else:
        path = os.path.expanduser(ask(L("path ของโฟลเดอร์ (กด Tab ช่วยเติมได้)", "Folder path (Tab completes)"), "."))
    path = os.path.abspath(path)
    if not os.path.isdir(path):
        print(red(L(f"  ไม่เจอโฟลเดอร์ {path}", f"  Folder not found: {path}")))
        sys.exit(1)
    guesses = detect_project(path)
    projs = list(PROJECTS)
    if guesses:
        k = choose(L(f"ดูเหมือนเป็น {guesses[0]} ใช่ไหม?", f"Looks like {guesses[0]}, right?"),
                   [L(f"ใช่ {guesses[0]}", f"Yes, {guesses[0]}"), L("เลือกเอง", "Choose myself")])
        proj = guesses[0] if k == 0 else projs[choose(L("เลือกโปรเจกต์", "Choose the project"), projs)]
    else:
        proj = projs[choose(L("เลือกโปรเจกต์", "Choose the project"), projs)]
    return proj, path, mine


def after_menu(proj, root, results, mine):
    """เมนูหลังตรวจเสร็จ"""
    while True:
        if mine:
            opts = [L("🌐  เปิดหน้าเว็บ (แก้โค้ดได้ · Ctrl+S บันทึก+ตรวจใหม่)", "🌐  Open the web editor (Ctrl+S saves + re-checks)"),
                    L("✏️   แก้ใน vim (]e ไปจุดถัดไป · Tab แก้ให้ · :w ตรวจใหม่)", "✏️   Edit in vim (]e next problem · Tab fix · :w re-check)"),
                    L("⚡  แก้อัตโนมัติทั้งหมด", "⚡  Auto-fix everything"),
                    L("🔄  ตรวจใหม่", "🔄  Check again"), L("✕   ออก", "✕   Quit")]
        else:
            opts = [L("🌐  เปิดหน้าเว็บ (ดูอย่างเดียว)", "🌐  Open the web report (read only)"),
                    L("🔄  ตรวจใหม่", "🔄  Check again"), L("✕   ออก", "✕   Quit")]
        k = choose(L("จะทำอะไรต่อ?", "What next?"), opts)
        act = (["web", "vim", "fix", "again", "quit"] if mine else ["report", "again", "quit"])[k]
        if act == "quit":
            return
        if act == "report":
            open_report(write_report(proj, root, results, summarize(results)[1], mine))
        elif act == "web":
            serve(proj, root, results)
        elif act == "vim":
            vim_edit(proj, root, results)
            results = grade(proj, root, mine=mine, web=False, interactive=False)
        elif act == "fix":
            if offer_fixes(root, results):
                results = grade(proj, root, mine=mine, web=False, interactive=False)
        elif act == "again":
            results = grade(proj, root, mine=mine, web=False, interactive=False)


# ───────────────────────── fix apply ─────────────────────────
BACKUP_STAMP = datetime.datetime.now().strftime("%m%d_%H%M%S")


def offer_fixes(root, results):
    todo = [r for r in results if r.get("fixed") or r.get("renames") or r.get("deletes")]
    if not todo:
        return False
    print("\n  " + bold(L("🔧 สิ่งที่แก้ให้อัตโนมัติได้", "🔧 Things that can be fixed automatically")))
    for r in todo:
        for a, b in r.get("renames", []):
            print(L(f"     {r['ex']}: เปลี่ยนชื่อ {a} → {b}", f"     {r['ex']}: rename {a} → {b}"))
        for d in r.get("deletes", []):
            print(L(f"     {r['ex']}: ลบไฟล์ขยะ {d}", f"     {r['ex']}: delete junk file {d}"))
        for fn, txt in (r.get("fixed") or {}).items():
            before = r["sources"].get(fn, "")
            if before == txt:
                continue
            diff = list(difflib.unified_diff(before.split("\n"), txt.split("\n"), lineterm="", n=0))
            changed = sum(1 for l in diff if l.startswith(("+", "-")) and not l.startswith(("+++", "---")))
            af = r.get("after_fix") or {}
            res = ""
            if af:
                res = L(" → หลังแก้: ", " → after fix: ") + ", ".join(x for x in [
                    (green("norm ✔") if af.get("norm") else red(L("norm ยังไม่ผ่าน", "norm still fails"))) if af.get("norm") is not None else "",
                    green(L("คอมไพล์ ✔", "compile ✔")) if af.get("compile") else red(L("คอมไพล์ยังไม่ผ่าน", "still does not compile")),
                    green(L("เทสต์ ✔", "tests ✔")) if af.get("tests") else yellow(L("เทสต์ยังไม่ผ่าน (ต้องแก้ logic เอง)", "tests still fail (fix the logic yourself)"))] if x)
            print(L(f"     {r['ex']}/{fn}: แก้ {changed} บรรทัด{res}", f"     {r['ex']}/{fn}: {changed} lines changed{res}"))
            body = [l for l in diff[2:] if not l.startswith("@@") and not re.match(r"^[+-]/\*.*\*/$", l)]
            if not has_header(before) and has_header(txt):
                print("        " + green(L("+ ใส่ 42 header", "+ add 42 header")))
            for l in body[:12]:
                if l.startswith("+"):
                    print("        " + green(l))
                elif l.startswith("-"):
                    print("        " + red(l))
            if len(body) > 12:
                print("        " + dim(L(f"... อีก {len(body) - 12} บรรทัด (ดูในหน้าเว็บ)", f"... {len(body) - 12} more lines (see the web page)")))
    try:
        a = input("\n  " + bold(L("แก้ไฟล์จริงให้เลยไหม?", "Apply these fixes to your files?")) + dim(L(" (ไฟล์เดิมสำรองไว้ที่ ~/grade_backups)", " (originals backed up in ~/grade_backups)")) + " (y/n): ").strip().lower()
    except EOFError:
        a = "n"
    if a not in ("y", "yes"):
        print(dim(L("  ไม่แก้ ดูแบบที่ถูกได้ในหน้าเว็บ (กด Tab)", "  Not changed. See the fixed version on the web page (press Tab)")))
        return False
    for r in todo:
        for d in r.get("deletes", []):
            p = os.path.join(root, d)
            if os.path.isfile(p):
                os.remove(p)
        for a_, b_ in r.get("renames", []):
            src, dst = os.path.join(root, a_), os.path.join(root, b_)
            if os.path.exists(src) and not os.path.exists(dst):
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                code, _ = run(["git", "mv", src, dst], cwd=root)
                if code != 0:
                    shutil.move(src, dst)
        for fn, txt in (r.get("fixed") or {}).items():
            p = os.path.join(root, r["ex"], fn)
            if not os.path.isfile(p) or read(p) == txt:
                continue
            bdir = os.path.join(os.path.expanduser("~"), "grade_backups", BACKUP_STAMP, r["ex"])
            os.makedirs(bdir, exist_ok=True)
            shutil.copy(p, os.path.join(bdir, fn))
            with open(p, "w", encoding="utf-8") as f:
                f.write(txt)
    print(green(L("  ✔ แก้แล้ว", "  ✔ Fixed")) + dim(L(f"  ไฟล์เดิมอยู่ที่ ~/grade_backups/{BACKUP_STAMP}/  อย่าลืม git add + commit + push", f"  Originals in ~/grade_backups/{BACKUP_STAMP}/  Remember git add + commit + push")))
    return True


# ───────────────────────── report ─────────────────────────
def git_summary(root, results):
    """สิ่งที่ยังไม่ได้ส่งจริง (เฉพาะงานตัวเอง): ไฟล์ยังไม่ push / แก้ค้าง / commit ที่ยังไม่ push"""
    out = {"not_pushed": [], "modified": [], "ahead": 0, "git": False}
    for r in results:
        fc = r.get("filecheck") or {}
        out["git"] = out["git"] or fc.get("git", False)
        for f in fc.get("required", []):
            if f["state"] in ("not_pushed", "modified"):
                out[f["state"]].append(f"{fc['dir']}/{f['name']}")
    g = git_info(root)
    if g and g.get("ahead"):
        out["ahead"] = g["ahead"]
    return out


def render_report(proj, root, results, last, editable=False, mine=False):
    tpl = read(os.path.join(LIB, "report.html"))
    data = {"proj": proj, "root": root, "time": datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
            "last_ok": last, "results": results, "kinds": {k: list(v) for k, v in KIND.items()},
            "lang": LANG, "editable": editable, "mine": mine or editable,
            "gitsum": git_summary(root, results) if (mine or editable) else None}
    js = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    return tpl.replace("/*__DATA__*/null", js)


def write_report(proj, root, results, last, mine=False):
    out_dir = os.path.join(os.path.expanduser("~"), "grade_reports")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, f"{proj}_{os.path.basename(root.rstrip('/'))}_{datetime.datetime.now():%m%d_%H%M%S}.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(render_report(proj, root, results, last, mine=mine))
    return out


def open_report(path):
    if sys.platform == "darwin":
        run(["open", path])
    elif have("xdg-open"):
        subprocess.Popen(["xdg-open", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def update():
    code, out = run(["git", "-C", HERE, "pull", "--ff-only"], timeout=60)
    print(green(L("  อัปเดตแล้ว ✔", "  Updated ✔")) if code == 0 else red(L("  อัปเดตไม่สำเร็จ: ", "  Update failed: ") + out))


# ───────────────────────── web editor (local server) ─────────────────────────
def spec_of(proj, ex):
    return next((s for s in PROJECTS[proj] if s["ex"] == ex), None)


def serve(proj, root, results):
    """เปิดหน้าเว็บที่แก้โค้ดได้ (เฉพาะงานตัวเอง) บน 127.0.0.1"""
    import threading
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    g = Grader(proj, root, mine=True)
    lock = threading.Lock()
    state = {"results": results}
    backed = set()

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _send(self, code, body, ctype="application/json"):
            data = body if isinstance(body, bytes) else body.encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", ctype + "; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if self.path.split("?")[0] != "/":
                return self._send(404, "{}")
            passed, last = summarize(state["results"])
            self._send(200, render_report(proj, root, state["results"], last, editable=True, mine=True), "text/html")

        def do_POST(self):
            try:
                n = int(self.headers.get("Content-Length", "0"))
                req = json.loads(self.rfile.read(n).decode("utf-8"))
                ex, fn, text = req.get("ex"), req.get("file"), req.get("text")
                spec = spec_of(proj, ex)
                idx = next(i for i, r in enumerate(state["results"]) if r["ex"] == ex)
                if not spec or fn not in state["results"][idx]["sources"]:
                    return self._send(400, json.dumps({"error": "bad file"}))
                with lock:
                    if self.path == "/api/save":
                        p = os.path.join(root, ex, fn)
                        if p not in backed and os.path.isfile(p):
                            bdir = os.path.join(os.path.expanduser("~"), "grade_backups", BACKUP_STAMP, ex)
                            os.makedirs(bdir, exist_ok=True)
                            shutil.copy(p, os.path.join(bdir, fn))
                            backed.add(p)
                        with open(p, "w", encoding="utf-8") as f:
                            f.write(text)
                        r = g.grade_ex(spec)
                        state["results"][idx] = r
                    else:
                        r = g.grade_ex(spec, override={fn: text})
                passed, last = summarize(state["results"])
                self._send(200, json.dumps({"result": r, "summary": [passed, len(state["results"]), last]},
                                           ensure_ascii=False))
            except Exception as e:  # noqa: BLE001
                self._send(500, json.dumps({"error": str(e)}))

    srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
    url = f"http://127.0.0.1:{srv.server_address[1]}/"
    print()
    box([L("🌐 หน้าเว็บแก้โค้ดเปิดอยู่ที่ ", "🌐 Web editor running at ") + c("4", url),
         dim(L("Ctrl+S = บันทึกและตรวจใหม่ · Tab บนบรรทัดแดง = แก้จุดนั้น", "Ctrl+S = save and re-check · Tab on a red line = fix it")),
         dim(L("กด Ctrl+C ที่นี่เพื่อกลับเมนู", "Press Ctrl+C here to go back to the menu"))])
    open_report(url)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print()
    finally:
        srv.server_close()
        g.cleanup()


# ───────────────────────── vim ─────────────────────────
def qf_lines(root, results):
    out = []
    for r in results:
        files = list(r["sources"]) or r["files"]
        for i in r["issues"]:
            fn = i.get("file") if i.get("file") in r["sources"] else (files[0] if files else None)
            if not fn:
                continue
            path = os.path.join(root, r["ex"], fn)
            if not os.path.isfile(path):
                continue
            label = KIND[i["kind"]][1]
            fx = " ⚡Tab" if i.get("fixable") else ""
            msg = f"[{r['ex']} {label}] {i['title']}{fx}"
            if i.get("hint"):
                msg += f" → {i['hint']}"
            if i["kind"] == "logic" and i.get("why"):
                msg += "  (" + i["why"].replace("\n", " | ") + ")"
            out.append(f"{path}:{i.get('line') or 1}:1: {msg}")
    return out


VIM_SCRIPT = r'''
set errorformat=%%f:%%l:%%c:\ %%m
set laststatus=2
set encoding=utf-8
let g:grader_cmd = %(cmd)s
let g:grader_proj = %(proj)s
let g:grader_root = %(root)s
function! GraderCount()
  return len(getqflist())
endfunction
set statusline=%%f\ %%m%%=\ ◆\ grader:\ %%{GraderCount()}\ %(problems)s\ \ ]e/[e\ Tab\ :w\
function! GraderFix()
  let ex = fnamemodify(expand('%%:p'), ':h:t')
  let fn = expand('%%:t')
  let before = getline(1, '$')
  let out = systemlist(g:grader_cmd . ' --fix-text ' . g:grader_proj . ' ' . ex . ' ' . shellescape(fn) . ' ' . shellescape(g:grader_root), before)
  if v:shell_error || out == before
    echo %(nofix)s
    return
  endif
  call setline(1, out)
  if line('$') > len(out)
    silent execute (len(out) + 1) . ',$delete _'
  endif
  echo %(fixed)s
endfunction
function! GraderRecheck()
  echo %(checking)s
  redraw
  cgetexpr system(g:grader_cmd . ' --qf ' . g:grader_proj . ' ' . shellescape(g:grader_root))
  redraw!
  echo printf(%(left)s, len(getqflist()))
endfunction
function! GraderShow()
  for e in getqflist()
    if e.bufnr == bufnr('%%') && e.lnum == line('.')
      echo strpart(e.text, 0, &columns - 2)
      return
    endif
  endfor
endfunction
nnoremap <silent> ]e :silent! cnext<CR>:call GraderShow()<CR>
nnoremap <silent> [e :silent! cprev<CR>:call GraderShow()<CR>
nnoremap <silent> <Tab> :call GraderFix()<CR>
nnoremap <silent> <F5> :call GraderRecheck()<CR>
augroup grader
  autocmd!
  autocmd BufWritePost *.c,*.h,Makefile,*.sh call GraderRecheck()
  autocmd CursorMoved * call GraderShow()
augroup END
echo %(help)s
'''


def vim_edit(proj, root, results):
    lines = qf_lines(root, results)
    if not lines:
        print(green(L("  ไม่มีจุดให้แก้ในไฟล์ 🎉", "  Nothing to fix in your files 🎉")))
        return
    if not have("vim"):
        print(red(L("  ไม่เจอ vim ในเครื่องนี้", "  vim is not installed")))
        return
    tmp = tempfile.mkdtemp(prefix="grader_vim_")
    qf = os.path.join(tmp, "qf.txt")
    with open(qf, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    vq = lambda s: "'" + s.replace("'", "''") + "'"
    cmd = f"{sys.executable} {os.path.abspath(__file__)}"
    script = VIM_SCRIPT % {
        "cmd": vq(cmd), "proj": vq(proj), "root": vq(root),
        "problems": L("จุด", "problems"),
        "nofix": vq(L("ไม่มีอะไรให้แก้อัตโนมัติในไฟล์นี้", "Nothing to auto-fix in this file")),
        "fixed": vq(L("⚡ แก้แล้ว (u = ย้อนกลับ, :w = บันทึก+ตรวจใหม่)", "⚡ Fixed (u = undo, :w = save + re-check)")),
        "checking": vq(L("กำลังตรวจใหม่...", "Re-checking...")),
        "left": vq(L("ตรวจแล้ว: เหลือ %d จุด  (]e ไปจุดถัดไป)", "Checked: %d problems left  (]e next)")),
        "help": vq(L("]e/[e = ไปจุดผิดถัดไป/ก่อนหน้า · Tab = แก้อัตโนมัติ · :w = บันทึก+ตรวจใหม่ · :q = ออก",
                     "]e/[e = next/previous problem · Tab = auto-fix · :w = save + re-check · :q = quit")),
    }
    vs = os.path.join(tmp, "grader.vim")
    with open(vs, "w", encoding="utf-8") as f:
        f.write(script)
    subprocess.call(["vim", "-q", qf, "-S", vs])
    shutil.rmtree(tmp, ignore_errors=True)


# ───────────────────────── main ─────────────────────────
def grade(proj, root, mine=False, web=True, fix=None, interactive=None, quiet=False):
    mine = mine and fix is not False
    g = Grader(proj, root, mine)
    if not quiet:
        print()
        print(L(f"  {bold('ตรวจ ' + proj)}  {dim(root)}", f"  {bold('Grading ' + proj)}  {dim(root)}"))
        print("  " + (c("36", L("🧑 งานของฉัน · แก้ไฟล์ได้", "🧑 My work · files can be edited")) if mine and fix is not False else
                      c("35", L("👥 งานเพื่อน · ดูอย่างเดียว ไม่แตะไฟล์ (ใช้ --fix ถ้าเป็นงานตัวเอง)", "👥 Peer's work · read only, files are never touched (use --fix if it is yours)"))))
        if not g.has_norm:
            print(yellow(L("  ⚠ ไม่เจอ norminette ในเครื่องนี้ ข้ามการเช็ก norm",
                           "  ⚠ norminette not found on this computer, skipping norm checks")))
        known = {e["ex"] for e in PROJECTS[proj]}
        for d in sorted(os.listdir(root)):
            if d not in known and not d.startswith(".") and not re.match(r"ex\d+", d, re.I):
                print(yellow(L(f"  ⚠ มีของเกินในโฟลเดอร์งาน: {d}", f"  ⚠ Extra item in the project folder: {d}")))
        print()
    results = []
    specs = PROJECTS[proj]
    try:
        for n, spec in enumerate(specs):
            if not quiet:
                progress(n, len(specs), spec["ex"])
            results.append(g.grade_ex(spec))
    finally:
        g.cleanup()
    if quiet:
        return results
    if TTY:
        sys.stdout.write("\r\033[2K")
    print_table(results)
    bad = [r for r in results if r["status"] != "OK"]
    if bad:
        print()
        for r in bad:
            print_details(r)
    print_tips(results)
    print_summary(results)
    passed, last = summarize(results)
    if mine:
        print_git_warnings(git_summary(root, results))
    if web:
        path = write_report(proj, root, results, last, mine)
        print(dim(L(f"  หน้าเว็บ: {path}", f"  Web report: {path}")))
        open_report(path)
    if interactive is None:
        interactive = sys.stdin.isatty() and TTY
    if interactive:
        after_menu(proj, root, results, mine and fix is not False)
    return results


def main(argv):
    if argv[:1] == ["--fix-text"] and len(argv) >= 5:
        proj, ex, fn, root = argv[1:5]
        text = sys.stdin.read()
        g = Grader(proj, os.path.abspath(root), mine=True)
        try:
            r = g.grade_ex(spec_of(proj, ex), override={fn: text})
        finally:
            g.cleanup()
        sys.stdout.write((r.get("fixed") or {}).get(fn, text))
        return
    if argv[:1] == ["--qf"] and len(argv) >= 3:
        results = grade(argv[1], os.path.abspath(argv[2]), quiet=True)
        print("\n".join(qf_lines(os.path.abspath(argv[2]), results)))
        return
    web = "--no-web" not in argv
    fix = True if "--fix" in argv else (False if "--peer" in argv else None)
    args = [a for a in argv if not a.startswith("--")]
    if not args:
        proj, root, mine = menu()
        grade(proj, root, mine=mine, web=False, fix=fix)
        return
    first = {k.upper(): k for k in PROJECTS}.get(args[0].upper(), args[0].upper())
    if first == "UPDATE":
        return update()
    if first in ("HELP", "-H"):
        print(__doc__)
        return
    if first not in PROJECTS:
        print(red(L(f"  ไม่รู้จักโปรเจกต์ {args[0]}", f"  Unknown project {args[0]}")) +
              dim(L(f"  (มี: {' '.join(PROJECTS)})", f"  (available: {' '.join(PROJECTS)})")))
        print(__doc__)
        sys.exit(1)
    target = args[1] if len(args) > 1 else "."
    mine = False
    if is_url(target):
        root = clone(target, first)
    else:
        root = os.path.abspath(os.path.expanduser(target))
        if not os.path.isdir(root):
            print(red(L(f"  ไม่เจอโฟลเดอร์ {root}", f"  Folder not found: {root}")))
            sys.exit(1)
        login = os.environ.get("USER", "")
        mine = bool(login) and any(f"By: {login} " in read(os.path.join(dp, f))
                                   for dp, _, fs in os.walk(root) if ".git" not in dp for f in fs if f.endswith(".c"))
        if fix:
            mine = True
    grade(first, root, mine=mine, web=web, fix=fix)


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except KeyboardInterrupt:
        print()
