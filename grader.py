#!/usr/bin/env python3
"""piscine-grader: ตัวตรวจ C Piscine 42 (C00–C09)

grade                      เปิดเมนู
grade C03 <โฟลเดอร์|ลิงก์ git> [--no-web] [--fix] [--peer]
grade update               อัปเดตตัวตรวจ
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
TTY = sys.stdout.isatty()


def c(code, s):
    return f"\033[{code}m{s}\033[0m" if TTY else s


def green(s): return c("32", s)
def red(s): return c("31", s)
def yellow(s): return c("33", s)
def blue(s): return c("36", s)
def bold(s): return c("1", s)
def dim(s): return c("2", s)


KIND = {
    "file": ("📁", "ไฟล์"),
    "rule": ("🚫", "กฎ"),
    "norm": ("📏", "Norm"),
    "compile": ("🔧", "คอมไพล์"),
    "logic": ("🧠", "ผลลัพธ์"),
    "crash": ("💥", "พัง/ค้าง"),
}


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
            out.append(f"ตัวที่ {i1 + 1}: '{wrong[i1:i2]}' ควรเป็น '{right[j1:j2]}'")
        elif op == "delete":
            out.append(f"ตัวที่ {i1 + 1}: มี '{wrong[i1:i2]}' เกินมา")
        elif op == "insert":
            out.append(f"ตัวที่ {i1 + 1}: ขาด '{right[j1:j2]}'")
    return ", ".join(out[:3])


def close_match(name, candidates, cutoff=0.7):
    m = difflib.get_close_matches(name, candidates, n=1, cutoff=cutoff)
    if m:
        return m[0]
    low = {x.lower(): x for x in candidates}
    return low.get(name.lower())


def issue(kind, title, why="", hint="", file=None, line=None, fixable=False):
    return {"kind": kind, "title": title, "why": why, "hint": hint, "file": file, "line": line,
            "fixable": fixable}


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


def fix_header(text, fname):
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
    pending = 0  # if/while/else ที่ไม่มี { ตามหลัง
    out = []
    for raw, m in zip(lines, masked):
        stripped = raw.strip()
        ms = m.strip()
        if not stripped or raw.startswith("/*") or raw.startswith("#") or (raw.startswith(" *") and "*/" in raw):
            out.append(raw if raw.startswith(("/*", "#")) else stripped)
            continue
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
            pending = 1 if not pending else pending
        elif ms.endswith(";") or ms.endswith("}"):
            pending = 0
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
    "INVALID_HEADER": ("ไม่มี 42 header หรือ header เสีย", "ใส่ header ใหม่ (vim: :Stdheader)", True),
    "SPACE_REPLACE_TAB": ("ใช้ Space ในที่ที่ต้องเป็น Tab", "ระหว่างชนิดตัวแปรกับชื่อ และย่อหน้า ต้องใช้ Tab", True),
    "TAB_REPLACE_SPACE": ("ใช้ Tab ในที่ที่ต้องเป็น Space", "", True),
    "SPACE_BEFORE_FUNC": ("ระหว่างชนิดกับชื่อฟังก์ชันต้องเป็น Tab", "เช่น void<Tab>ft_putchar(...)", True),
    "TOO_FEW_TAB": ("ย่อหน้าไม่พอ", "ข้างใน { } ต้องย่อหน้าเพิ่ม 1 Tab ต่อชั้น", True),
    "TOO_MANY_TAB": ("ย่อหน้าเกิน", "", True),
    "MIXED_SPACE_TAB": ("ย่อหน้าปน Space กับ Tab", "ใช้ Tab อย่างเดียว", True),
    "SPC_BEFORE_NL": ("มี Space ท้ายบรรทัด", "ลบช่องว่างท้ายบรรทัด", True),
    "SPACE_EMPTY_LINE": ("บรรทัดว่างมี Space/Tab ค้าง", "", True),
    "CONSECUTIVE_NEWLINES": ("มีบรรทัดว่างติดกันหลายบรรทัด", "เหลือบรรทัดว่างได้แค่ 1", True),
    "CONSECUTIVE_SPC": ("มี Space ติดกันหลายตัว", "", True),
    "EMPTY_LINE_EOF": ("มีบรรทัดว่างท้ายไฟล์", "", True),
    "EMPTY_LINE_FUNCTION": ("มีบรรทัดว่างในฟังก์ชัน", "บรรทัดว่างในฟังก์ชันมีได้ที่เดียวคือหลังประกาศตัวแปร", True),
    "BRACE_NEWLINE": ("{ ต้องอยู่บรรทัดใหม่ของตัวเอง", "", True),
    "BRACE_SHOULD_EOL": ("หลัง { หรือ } ต้องขึ้นบรรทัดใหม่", "", True),
    "RETURN_PARENTHESIS": ("ค่าที่ return ต้องอยู่ในวงเล็บ", "เขียนเป็น return (x);", True),
    "SPACE_AFTER_KW": ("หลัง if/while/return ต้องเว้น 1 Space", "เขียนเป็น if (...)", True),
    "NL_AFTER_VAR_DECL": ("หลังประกาศตัวแปรต้องเว้น 1 บรรทัด", "", True),
    "NL_AFTER_PREPROC": ("หลัง #include ต้องเว้นบรรทัด", "", True),
    "MISALIGNED_VAR_DECL": ("ชื่อตัวแปรไม่ตรงคอลัมน์เดียวกัน", "ใช้ Tab จัดชื่อตัวแปรให้ตรงกัน", True),
    "MISALIGNED_FUNC_DECL": ("ชื่อฟังก์ชันไม่ตรงคอลัมน์", "", True),
    "SPC_AFTER_OPERATOR": ("หลังเครื่องหมาย (+ - = ...) ต้องเว้น Space", "เช่น a = b + 1", False),
    "SPC_BFR_OPERATOR": ("ก่อนเครื่องหมาย (+ - = ...) ต้องเว้น Space", "", False),
    "NO_SPC_AFR_OPR": ("หลังเครื่องหมายห้ามเว้น Space", "", False),
    "NO_SPC_BFR_OPR": ("ก่อนเครื่องหมายห้ามเว้น Space", "", False),
    "SPC_AFTER_PAR": ("หลัง ( ห้ามเว้น Space", "", False),
    "SPC_BFR_PAR": ("ก่อน ) ห้ามเว้น Space", "", False),
    "NO_ARGS_VOID": ("ฟังก์ชันที่ไม่รับค่าต้องเขียน (void)", "เช่น void ft_print_alphabet(void)", False),
    "TOO_MANY_LINES": ("ฟังก์ชันยาวเกิน 25 บรรทัด", "แยกบางส่วนออกเป็นฟังก์ชันย่อย", False),
    "TOO_MANY_FUNCS": ("มีฟังก์ชันเกิน 5 ตัวในไฟล์", "", False),
    "TOO_MANY_VARS_FUNC": ("ประกาศตัวแปรเกิน 5 ตัวในฟังก์ชัน", "ย้ายบางส่วนไปฟังก์ชันย่อย", False),
    "TOO_MANY_ARGS": ("ฟังก์ชันรับ argument เกิน 4 ตัว", "", False),
    "LINE_TOO_LONG": ("บรรทัดยาวเกิน 80 ตัวอักษร", "ตัดขึ้นบรรทัดใหม่", False),
    "FORBIDDEN_CS": ("ใช้คำสั่งต้องห้าม (for, do...while, switch, goto)", "เปลี่ยนเป็น while", False),
    "TERNARY_FBIDDEN": ("ห้ามใช้ ? : (ternary)", "เปลี่ยนเป็น if/else", False),
    "VAR_DECL_START_FUNC": ("ต้องประกาศตัวแปรไว้ต้นฟังก์ชันเท่านั้น", "", False),
    "DECL_ASSIGN_LINE": ("ห้ามประกาศตัวแปรพร้อมกำหนดค่า", "แยกเป็น int i; แล้วค่อย i = 0;", False),
    "MULT_DECL_LINE": ("ห้ามประกาศหลายตัวแปรในบรรทัดเดียว", "", False),
    "TOO_MANY_INSTR": ("มีหลายคำสั่งในบรรทัดเดียว", "1 บรรทัด 1 คำสั่ง", False),
    "WRONG_SCOPE_COMMENT": ("ห้ามเขียน comment ข้างในฟังก์ชัน", "ย้าย comment ไปไว้นอกฟังก์ชัน", False),
    "FORBIDDEN_CHAR_NAME": ("ชื่อตัวแปร/ฟังก์ชันต้องเป็นตัวเล็ก ตัวเลข หรือ _ เท่านั้น", "", False),
    "USER_DEFINED_TYPEDEF": ("ชื่อ typedef ต้องขึ้นต้นด้วย t_", "", False),
    "STRUCT_TYPE_NAMING": ("ชื่อ struct ต้องขึ้นต้นด้วย s_", "", False),
    "HEADER_PROT_ALL": ("header ต้องมี #ifndef ... #define ... #endif ป้องกัน include ซ้ำ", "", False),
    "HEADER_PROT_NAME": ("ชื่อ macro ป้องกัน header ต้องเป็น ชื่อไฟล์_H ตัวใหญ่", "เช่น FT_H", False),
    "PREPROC_CONSTANT": ("#define ต้องเป็นค่าคงที่เท่านั้น", "", False),
    "MACRO_NAME_CAPITAL": ("ชื่อ macro ต้องเป็นตัวใหญ่", "", False),
    "PREPROC_BAD_INDENT": ("#define ใน #ifndef ต้องเว้น 1 Space หลัง #", "เขียนเป็น # define", False),
    "INCLUDE_START_FILE": ("#include ต้องอยู่ต้นไฟล์", "", False),
    "GLOBAL_VAR_DETECTED": ("ห้ามใช้ตัวแปร global", "", False),
    "EXP_PARENTHESIS": ("ต้องมีช่องว่างก่อน (", "", False),
}


def parse_norm(out, fname):
    issues = []
    for m in re.finditer(r"Error:\s+(\w+)\s+\(line:\s*(\d+),\s*col:\s*(\d+)\):\s*(.*)", out):
        code, ln, _col, msg = m.group(1), int(m.group(2)), m.group(3), re.sub(r"\x1b\[[0-9;]*m", "", m.group(4))
        th = NORM_TH.get(code)
        title = th[0] if th else msg.strip()
        hint = th[1] if th else ""
        issues.append(issue("norm", title, why=f"{code}: {msg.strip()}", hint=hint, file=fname, line=ln,
                            fixable=bool(th and th[2])))
    return issues


# ───────────────────────── compiler messages ─────────────────────────
def explain_cc(msg):
    """แปลข้อความ error ของ gcc/clang เป็นคำอธิบายภาษาไทย → (title, hint, fix_kind)"""
    m = msg
    rules = [
        (r"expected ';'|expected ',' or ';'", "ลืม ; ท้ายคำสั่ง", "ใส่ ; ที่ท้ายบรรทัดก่อนหน้าบรรทัดนี้", "semicolon"),
        (r"expected '\)' before (numeric constant|'&'|'\w+'|string constant|character constant)|expected ',' or '\)'|^expected '\)'$",
         "ลืม , คั่นระหว่างค่าที่ส่งให้ฟังก์ชัน", "เช่น write(1, &c, 1) ต้องมี , ครบทุกช่อง", "comma"),
        (r"implicit declaration of function '?write'?|call to undeclared function 'write'",
         "เรียก write แต่ไม่ได้ #include <unistd.h>", "ใส่ #include <unistd.h> ไว้บนสุด", "inc_unistd"),
        (r"implicit declaration of function '?(malloc|free)'?|call to undeclared (library )?function '(malloc|free)'",
         "เรียก malloc/free แต่ไม่ได้ #include <stdlib.h>", "ใส่ #include <stdlib.h>", "inc_stdlib"),
        (r"implicit declaration of function|call to undeclared function",
         "เรียกฟังก์ชันที่ยังไม่ได้ประกาศ", "ต้องเขียนฟังก์ชันนั้นไว้ข้างบน หรือใส่ prototype", None),
        (r"redeclared as different kind of symbol|redefinition of '(\w+)'.*|redefinition of parameter",
         "ประกาศตัวแปรชื่อซ้ำกับ parameter", "ตัวแปรนี้มีมาให้แล้วในวงเล็บของฟังก์ชัน ไม่ต้องประกาศใหม่", "redecl"),
        (r"'(\w+)' undeclared|use of undeclared identifier '(\w+)'",
         "ใช้ชื่อที่ไม่มีอยู่ (ยังไม่ได้ประกาศ หรือพิมพ์ผิด)",
         "ถ้าหมายถึงตัวอักษร ต้องใส่ ' ' เช่น 'A' / ถ้าเป็นตัวแปร ต้องประกาศก่อน", "undeclared"),
        (r"unused variable", "ประกาศตัวแปรแล้วไม่ได้ใช้ (-Werror ถือว่าเป็น error)", "ลบตัวแปรนั้นทิ้ง", None),
        (r"unused parameter", "parameter ไม่ได้ถูกใช้เลย", "ใช้มันในฟังก์ชัน หรือเขียน (void)ชื่อ;", None),
        (r"conflicting types", "prototype ไม่ตรงกับตัวฟังก์ชัน", "ชนิดของ return/parameter ต้องตรงกันทั้งสองที่",
         None),
        (r"control reaches end of non-void function|non-void function does not return",
         "ฟังก์ชันที่ต้องคืนค่า แต่บางทางไม่มี return", "ใส่ return (...); ให้ครบทุกทาง", None),
        (r"expected declaration or statement at end of input|expected '}'", "ปีกกา { } ไม่ครบคู่",
         "นับ { กับ } ให้เท่ากัน", None),
        (r"expected identifier or '\('|expected expression", "เขียนคำสั่งผิดรูปแบบตรงนี้",
         "ดูเครื่องหมายรอบ ๆ ตำแหน่งนี้ (วงเล็บ, ;, ,)", None),
        (r"comparison between pointer and integer|makes integer from pointer|makes pointer from integer",
         "ใช้ pointer กับตัวเลขปนกัน", "ตัวอักษรเดียวใช้ ' ' ส่วนข้อความใช้ \" \"", None),
        (r"too few arguments", "ส่งค่าให้ฟังก์ชันไม่ครบ", "", None),
        (r"too many arguments", "ส่งค่าให้ฟังก์ชันเกิน", "", None),
        (r"suggest parentheses", "ควรใส่วงเล็บครอบเงื่อนไข", "เช่น if ((a = b))", None),
        (r"is used uninitialized|may be used uninitialized", "ใช้ตัวแปรก่อนกำหนดค่า", "กำหนดค่าเริ่มต้นก่อนใช้",
         None),
        (r"stray '\\\d+'|stray '", "มีตัวอักษรแปลก ๆ ในโค้ด (อาจเป็นสระไทยหรือเครื่องหมายพิเศษ)", "", None),
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
        issues.append(issue("compile", title, why=msg, hint=hint, file=os.path.basename(fname), line=ln,
                            fixable=fixable))
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
            hints.append(h["hint"])
    for cs in bad:
        e, g = cs.get("exp", ""), cs.get("got", "")
        if g in ('""', "") and e not in ('""', ""):
            hints.append("ฟังก์ชันไม่ได้พิมพ์/คืนอะไรออกมาเลย เช็กว่าเรียก write หรือ return ค่าจริงไหม")
        elif g.startswith(e.rstrip('"')) and len(g) > len(e):
            hints.append("ผลลัพธ์มีของเกินท้าย เช่น , หรือขึ้นบรรทัดใหม่เกิน")
        elif e.startswith(g.rstrip('"')) and len(e) > len(g):
            hints.append("ผลลัพธ์ขาดท้าย เช่น ลืมตัวสุดท้าย หรือเงื่อนไข while หยุดเร็วไป 1 รอบ")
    if status == "TIMEOUT":
        hints.append("โปรแกรมวนไม่จบ: ลืมเพิ่มค่า i++ หรือเงื่อนไข while ไม่มีวันเป็นเท็จ")
    if status == "CRASH":
        hints.append("โปรแกรมพัง (segfault): อ่านเกินขอบ string/array, ใช้ pointer ที่เป็น NULL หรือลืม malloc")
    out = []
    for h in hints:
        if h not in out:
            out.append(h)
    return out[:4]


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


# ───────────────────────── one exercise ─────────────────────────
class Grader:
    def __init__(self, proj, root, mine=False):
        self.proj = proj
        self.root = root
        self.mine = mine
        self.tests = os.path.join(TESTS, proj)
        self.work = tempfile.mkdtemp(prefix="grader_")
        self.has_norm = have("norminette")

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
            for fn in spec["files"]:
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
                    cs["got"] = "พัง/ค้าง" if code == "TIMEOUT" or (isinstance(code, int) and code < 0) else "$\n".join(got.split("\n"))
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
            cases = [{"name": "sh libft_creator.sh สร้าง libft.a", "ok": os.path.isfile(os.path.join(sd, "libft.a"))}]
            if not cases[0]["ok"]:
                cases[0].update(exp="มีไฟล์ libft.a", got=out.strip() or "ไม่มีไฟล์")
                return "KO", "", "", cases
            exe = os.path.join(wd, "t")
            code, out = run(["cc", "-w", "-I", LIB, os.path.join(self.tests, "ex00.c"), "-L", sd, "-lft", "-o", exe])
            if code != 0:
                cases.append({"name": "ลิงก์กับ libft.a", "ok": False, "exp": "ฟังก์ชันครบ 5 ตัว", "got": out[-300:]})
                return "KO", "", "", cases
            st, a, b, more = self._run_test([exe], "")
            return st, a, b, cases + more
        if t == "make":
            return self._run_make(wd, srcs)
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
        chk("make สร้าง libft.a", os.path.isfile(lib), "มี libft.a", o1[-300:])
        chk("make แสดงคำสั่ง cc พร้อม -Wall -Wextra -Werror",
            all(x in o1 for x in ("-Wall", "-Wextra", "-Werror")), "เห็น flag ครบ", o1[-300:])
        chk(".o อยู่ข้าง .c ใน srcs/", os.path.isfile(os.path.join(m, "srcs", "ft_putchar.o")))
        _, nm = run(["nm", lib])
        n = len(set(re.findall(r" T _?(ft_putchar|ft_swap|ft_putstr|ft_strlen|ft_strcmp)$", nm, re.M)))
        chk("libft.a มีครบ 5 ฟังก์ชัน", n == 5, "5", str(n))
        o2 = mk()
        chk("รัน make ซ้ำ ไม่คอมไพล์ใหม่", not re.search(r"(^|\s)(cc|gcc|ar)\s", o2), "ไม่มีคำสั่ง cc/ar", o2[-200:])
        mk("clean")
        chk("make clean ลบ .o แต่ libft.a ยังอยู่",
            not any(f.endswith(".o") for f in os.listdir(os.path.join(m, "srcs"))) and os.path.isfile(lib))
        mk("fclean")
        chk("make fclean ลบ libft.a", not os.path.isfile(lib))
        mk("re")
        chk("make re สร้างใหม่ได้", os.path.isfile(lib))
        return ("OK" if all(c["ok"] for c in cases) else "KO"), "", "", cases

    # ---- main entry per exercise ----
    def grade_ex(self, spec):
        ex = spec["ex"]
        res = {"ex": ex, "files": spec["files"], "issues": [], "cases": [], "sources": {}, "fixed": {},
               "solution": {}, "hints": [], "renames": [], "deletes": [], "status": "OK", "after_fix": None}
        exdir = os.path.join(self.root, ex)
        top = [d for d in os.listdir(self.root) if os.path.isdir(os.path.join(self.root, d))]
        if not os.path.isdir(exdir):
            near = close_match(ex, [d for d in top if d not in [e["ex"] for e in PROJECTS[self.proj]]], 0.6)
            if near:
                res["issues"].append(issue("file", f"ชื่อโฟลเดอร์ผิด: {near} → ควรเป็น {ex}", why=char_diff(near, ex),
                                           fixable=True))
                res["renames"].append((near, ex))
                exdir = os.path.join(self.root, near)
            else:
                res["issues"].append(issue("file", f"ไม่มีโฟลเดอร์ {ex}", hint="ยังไม่ได้ทำ หรือยังไม่ได้ push ข้อนี้"))
                res["status"] = "ไม่มีไฟล์"
                self._solution(res, spec)
                return res
        present = sorted(os.listdir(exdir))
        srcs = {}
        used = set()
        for fn in spec["files"]:
            if fn in present:
                srcs[fn] = read(os.path.join(exdir, fn))
                used.add(fn)
                continue
            near = close_match(fn, [p for p in present if p not in spec["files"]])
            if near:
                res["issues"].append(issue("file", f"ชื่อไฟล์ผิด: {near} → ควรเป็น {fn}", why=char_diff(near, fn),
                                           hint="Moulinette หาไฟล์จากชื่อเป๊ะ ๆ ถ้าชื่อผิดจะได้ 0 ทั้งข้อ",
                                           file=near, fixable=True))
                res["renames"].append((f"{os.path.basename(exdir)}/{near}", f"{ex}/{fn}"))
                srcs[fn] = read(os.path.join(exdir, near))
                used.add(near)
            else:
                res["issues"].append(issue("file", f"ไม่มีไฟล์ {fn}", hint="ยังไม่ได้ทำ หรือยังไม่ได้ push ข้อนี้"))
        junk = ("a.out", ".DS_Store")
        for p in present:
            if p in used:
                continue
            is_junk = p in junk or p.endswith((".o", ".gch", ".swp", ".bak", "~")) or p.startswith(".")
            res["issues"].append(issue("file", f"มีไฟล์เกินใน {ex}: {p}",
                                       hint="โจทย์ห้ามมีไฟล์อื่น ลบออกด้วย git rm ก่อน push", fixable=is_junk))
            if is_junk:
                res["deletes"].append(f"{os.path.basename(exdir)}/{p}")
        res["sources"] = dict(srcs)
        if len(srcs) < len(spec["files"]):
            res["status"] = "ไม่มีไฟล์"
            self._solution(res, spec)
            return res

        # header / main / forbidden  (แก้คอมไพล์ก่อน เพราะเลขบรรทัดอ้างอิงไฟล์เดิม)
        fixed = {fn: (self._fix_compile(fn, t, exdir) if fn.endswith(".c") else t) for fn, t in srcs.items()}
        for fn, txt in srcs.items():
            if not has_header(txt):
                res["issues"].append(issue("rule", "ไม่มี 42 header", hint="vim: พิมพ์ :Stdheader", file=fn, line=1,
                                           fixable=True))
                fixed[fn] = fix_header(fixed[fn], fn)
            if fn.endswith(".c") and spec["type"] != "prog" and main_line(txt):
                res["issues"].append(issue("rule", "มีฟังก์ชัน main ในไฟล์ (ห้ามมี)",
                                           hint="ลบ main ออก ใช้ main ทดสอบในไฟล์อื่นที่ไม่ได้ push",
                                           file=fn, line=main_line(txt), fixable=True))
                fixed[fn] = fix_remove_main(fixed[fn])

        # norminette
        norm_issues = self._norm(srcs, exdir)
        if any(i["title"] == "ไม่มี 42 header" for i in res["issues"]):
            norm_issues = [i for i in norm_issues if not i["why"].startswith("INVALID_HEADER")]
        res["issues"] += norm_issues
        if any(i["fixable"] for i in norm_issues):
            for fn in fixed:
                if fn.endswith((".c", ".h")):
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
                res["issues"].append(issue("compile", "คอมไพล์ไม่ผ่าน" if status == "COMPILE" else
                                           "ชื่อฟังก์ชันหรือ prototype ไม่ตรงโจทย์", why=cc_out.strip()[-600:]))
            res["status"] = "คอมไพล์ไม่ผ่าน" if status == "COMPILE" else "ใช้กับตัวเทสต์ไม่ได้"
        else:
            res["issues"] += self._forbidden(spec, srcs)
            res["cases"] = cases
            if status == "TIMEOUT":
                res["issues"].append(issue("crash", f"ค้างเกิน {TIMEOUT} วินาที", hint="วนไม่จบ"))
            elif status == "CRASH":
                res["issues"].append(issue("crash", "โปรแกรมพัง (crash/segfault)"))
            for cs in cases:
                if not cs["ok"]:
                    res["issues"].append(issue("logic", cs["name"], why=f"ควรได้: {cs.get('exp', '')}\nได้จริง: {cs.get('got', '')}"))
            if status != "OK":
                res["status"] = {"KO": "ผลลัพธ์ผิด", "TIMEOUT": "ค้าง", "CRASH": "พัง"}.get(status, status)
            if status != "OK":
                res["hints"] = guess_hints(self.proj, ex, cases, status)
        if res["status"] == "OK" and any(i["kind"] in ("file", "rule", "norm") for i in res["issues"]):
            res["status"] = "ผิดกฎ/Norm"
        if res["status"] == "OK" and res["renames"]:
            res["status"] = "ชื่อไฟล์ผิด"

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
        allowed = set(spec["allowed"])
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
            issues.append(issue("rule", f"ใช้ฟังก์ชันต้องห้าม: {shown}",
                                hint=f"ข้อนี้อนุญาตแค่: {', '.join(spec['allowed']) or 'ไม่มีเลย'}",
                                file=ln[1] if ln else None, line=ln[0] if ln else None))
        return issues

    def _verify_fixed(self, spec, fixed, exdir):
        out = {}
        norm = self._norm(fixed, exdir) if self.has_norm else []
        out["norm"] = len(norm) == 0 if self.has_norm else None
        out["norm_left"] = [f"บรรทัด {i['line']}: {i['title']}" for i in norm][:6]
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


# ───────────────────────── terminal output ─────────────────────────
BANNER = r"""
  ╔════════════════════════════════════════════╗
  ║     ◆  PISCINE GRADER  ·  42 BANGKOK  ◆    ║
  ╚════════════════════════════════════════════╝"""


def print_ex(r):
    ok = r["status"] == "OK"
    n_ok = sum(1 for c in r["cases"] if c["ok"])
    cnt = f"{n_ok}/{len(r['cases'])} เคส" if r["cases"] else ""
    head = f"  {bold(r['ex'])}  {dim(', '.join(r['files']))}"
    tag = green("✔ ผ่าน") if ok else red("✘ " + r["status"])
    print(f"{head}  {dim(cnt)}  {tag}")
    if ok:
        return
    shown = 0
    by_kind = {}
    for i in r["issues"]:
        by_kind.setdefault(i["kind"], []).append(i)
    for kind in ("file", "rule", "compile", "crash", "norm", "logic"):
        items = by_kind.get(kind, [])
        if not items:
            continue
        icon, label = KIND[kind]
        limit = 6 if kind != "norm" else 8
        for i in items[:limit]:
            where = f"บรรทัด {i['line']}: " if i.get("line") else ""
            fx = dim("  [แก้อัตโนมัติได้]") if i.get("fixable") else ""
            print(f"     {icon} {yellow(label.ljust(9))} {where}{i['title']}{fx}")
            if kind == "logic" and i.get("why"):
                for l in i["why"].split("\n")[:2]:
                    print(f"                  {dim(l[:110])}")
            elif kind == "file" and i.get("why"):
                print(f"                  {dim('→ ' + i['why'])}")
            elif i.get("hint") and kind in ("file", "compile", "rule"):
                print(f"                  {dim('→ ' + i['hint'])}")
            shown += 1
        if len(items) > limit:
            print(f"                  {dim(f'...และอีก {len(items) - limit} จุด (ดูในหน้าเว็บ)')}")
    for h in r["hints"][:2]:
        print(f"     💡 {blue(h)}")


def summarize(results):
    passed = sum(1 for r in results if r["status"] == "OK")
    last = "ไม่มี"
    for r in results:
        if r["status"] != "OK":
            break
        last = r["ex"]
    return passed, last


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


def choose(title, options, default=0):
    """เมนูเลือกด้วยลูกศร ↑↓ + Enter (ถ้าไม่ใช่ terminal ใช้พิมพ์ตัวเลขแทน)"""
    print("\n  " + bold(title))
    if not (sys.stdin.isatty() and TTY):
        for i, o in enumerate(options):
            print(f"    {i + 1}) {o}")
        try:
            k = int(input("  เลือกหมายเลข: ").strip() or default + 1) - 1
        except ValueError:
            k = default
        return max(0, min(k, len(options) - 1))
    idx = default
    print(dim("  (↑↓ เลือก, Enter ตกลง, q ออก)"))

    def draw(first=False):
        if not first:
            sys.stdout.write(f"\033[{len(options)}A")
        for i, o in enumerate(options):
            mark = blue("❯ ") + bold(o) if i == idx else "  " + o
            sys.stdout.write("\033[2K    " + mark + "\n")
        sys.stdout.flush()

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


def ask(prompt, default=""):
    try:
        import readline  # noqa: F401  (ให้กด Tab เติมชื่อโฟลเดอร์ได้)
        readline.set_completer_delims(" \t\n")
        readline.parse_and_bind("tab: complete")
        import glob

        def comp(text, state):
            m = glob.glob(os.path.expanduser(text) + "*")
            m = [x + "/" if os.path.isdir(x) else x for x in m]
            return m[state] if state < len(m) else None

        readline.set_completer(comp)
    except ImportError:
        pass
    try:
        v = input("  " + prompt + (dim(f" [{default}]") if default else "") + ": ").strip()
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
            if d.startswith(".") or not os.path.isdir(p) or d in ("grade_eval", "piscine-grader"):
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
    print(dim(f"  กำลัง clone ไปที่ {dest} ..."))
    code, out = run(["git", "clone", "-q", url, dest], timeout=120)
    if code != 0:
        print(red("  clone ไม่สำเร็จ: ") + out.strip()[-300:])
        print(dim("  เช็กลิงก์อีกที หรือเครื่องนี้ยังไม่ได้ตั้ง SSH key กับ intra"))
        sys.exit(1)
    return dest


def is_url(s):
    return bool(re.match(r"^(\S+@\S+:|https?://)", s)) or s.endswith(".git")


def menu():
    print(c("36;1", BANNER))
    who = choose("จะตรวจงานของใคร?", ["งานของฉันเอง", "งานเพื่อน (วางลิงก์ git จากหน้า eval)",
                                      "เลือกโฟลเดอร์เอง", "อัปเดตตัวตรวจ", "ออก"])
    if who == 4:
        sys.exit(0)
    if who == 3:
        update()
        sys.exit(0)
    mine = who == 0
    if who == 0:
        works = find_my_work()
        opts = [f"{os.path.basename(p):<28} {dim(pr):<6} {dim(datetime.datetime.fromtimestamp(t).strftime('%d/%m %H:%M'))}"
                for t, p, pr in works] + ["พิมพ์ path เอง"]
        k = choose("เลือกโฟลเดอร์งาน (เรียงจากที่แก้ล่าสุด)", opts)
        path = works[k][1] if k < len(works) else os.path.expanduser(ask("path ของโฟลเดอร์ (กด Tab ช่วยเติมได้)"))
    elif who == 1:
        url = ask("วางลิงก์ git ของเพื่อน")
        path = clone(url) if is_url(url) else os.path.expanduser(url)
    else:
        path = os.path.expanduser(ask("path ของโฟลเดอร์ (กด Tab ช่วยเติมได้)", "."))
    path = os.path.abspath(path)
    if not os.path.isdir(path):
        print(red(f"  ไม่เจอโฟลเดอร์ {path}"))
        sys.exit(1)
    guesses = detect_project(path)
    projs = list(PROJECTS)
    if guesses:
        k = choose(f"ดูเหมือนเป็น {guesses[0]} ใช่ไหม?", [f"ใช่ {guesses[0]}", "เลือกเอง"])
        proj = guesses[0] if k == 0 else projs[choose("เลือกโปรเจกต์", projs)]
    else:
        proj = projs[choose("เลือกโปรเจกต์", projs)]
    return proj, path, mine


# ───────────────────────── fix apply ─────────────────────────
BACKUP_STAMP = datetime.datetime.now().strftime("%m%d_%H%M%S")


def offer_fixes(root, results):
    todo = [r for r in results if r.get("fixed") or r.get("renames") or r.get("deletes")]
    if not todo:
        return False
    print("\n  " + bold("🔧 สิ่งที่แก้ให้อัตโนมัติได้"))
    for r in todo:
        for a, b in r.get("renames", []):
            print(f"     {r['ex']}: เปลี่ยนชื่อ {a} → {b}")
        for d in r.get("deletes", []):
            print(f"     {r['ex']}: ลบไฟล์ขยะ {d}")
        for fn, txt in (r.get("fixed") or {}).items():
            before = r["sources"].get(fn, "")
            if before == txt:
                continue
            diff = list(difflib.unified_diff(before.split("\n"), txt.split("\n"), lineterm="", n=0))
            changed = sum(1 for l in diff if l.startswith(("+", "-")) and not l.startswith(("+++", "---")))
            af = r.get("after_fix") or {}
            res = ""
            if af:
                res = " → หลังแก้: " + ", ".join(x for x in [
                    (green("norm ✔") if af.get("norm") else red("norm ยังไม่ผ่าน")) if af.get("norm") is not None else "",
                    green("คอมไพล์ ✔") if af.get("compile") else red("คอมไพล์ยังไม่ผ่าน"),
                    green("เทสต์ ✔") if af.get("tests") else yellow("เทสต์ยังไม่ผ่าน (ต้องแก้ logic เอง)")] if x)
            print(f"     {r['ex']}/{fn}: แก้ {changed} บรรทัด{res}")
            body = [l for l in diff[2:] if not l.startswith("@@") and not re.match(r"^[+-]/\*.*\*/$", l)]
            if not has_header(before) and has_header(txt):
                print("        " + green("+ ใส่ 42 header"))
            for l in body[:12]:
                if l.startswith("+"):
                    print("        " + green(l))
                elif l.startswith("-"):
                    print("        " + red(l))
            if len(body) > 12:
                print("        " + dim(f"... อีก {len(body) - 12} บรรทัด (ดูในหน้าเว็บ)"))
    try:
        a = input("\n  " + bold("แก้ไฟล์จริงให้เลยไหม?") + dim(" (ไฟล์เดิมสำรองไว้ที่ ~/grade_backups)") + " (y/n): ").strip().lower()
    except EOFError:
        a = "n"
    if a not in ("y", "yes"):
        print(dim("  ไม่แก้ ดูแบบที่ถูกได้ในหน้าเว็บ (กด Tab)"))
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
    print(green("  ✔ แก้แล้ว") + dim(f"  ไฟล์เดิมอยู่ที่ ~/grade_backups/{BACKUP_STAMP}/  อย่าลืม git add + commit + push"))
    return True


# ───────────────────────── report ─────────────────────────
def write_report(proj, root, results, last):
    tpl = read(os.path.join(LIB, "report.html"))
    data = {"proj": proj, "root": root, "time": datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
            "last_ok": last, "results": results, "kinds": {k: list(v) for k, v in KIND.items()}}
    js = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    out_dir = os.path.join(os.path.expanduser("~"), "grade_reports")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, f"{proj}_{os.path.basename(root.rstrip('/'))}_{datetime.datetime.now():%m%d_%H%M%S}.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(tpl.replace("/*__DATA__*/null", js))
    return out


def open_report(path):
    if sys.platform == "darwin":
        run(["open", path])
    elif have("xdg-open"):
        subprocess.Popen(["xdg-open", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def update():
    code, out = run(["git", "-C", HERE, "pull", "--ff-only"], timeout=60)
    print(green("  อัปเดตแล้ว ✔") if code == 0 else red("  อัปเดตไม่สำเร็จ: " + out))


# ───────────────────────── main ─────────────────────────
def grade(proj, root, mine=False, web=True, fix=None):
    g = Grader(proj, root, mine)
    print()
    print(f"  {bold('ตรวจ ' + proj)}  {dim(root)}")
    if not g.has_norm:
        print(yellow("  ⚠ ไม่เจอ norminette ในเครื่องนี้ ข้ามการเช็ก norm"))
    known = {e["ex"] for e in PROJECTS[proj]}
    extra = [d for d in sorted(os.listdir(root)) if d not in known and not d.startswith(".")
             and not re.match(r"ex\d+", d, re.I)]
    for d in extra:
        print(yellow(f"  ⚠ มีของเกินในโฟลเดอร์งาน: {d}"))
    print()
    results = []
    try:
        for spec in PROJECTS[proj]:
            if TTY:
                sys.stdout.write(dim(f"  ⏳ กำลังตรวจ {spec['ex']} ...") + "\r")
                sys.stdout.flush()
            r = g.grade_ex(spec)
            if TTY:
                sys.stdout.write("\r\033[2K")
            print_ex(r)
            results.append(r)
    finally:
        g.cleanup()
    passed, last = summarize(results)
    bar = "".join(green("■") if r["status"] == "OK" else red("■") for r in results)
    print()
    print(f"  {bold('สรุป')}  {bar}  ผ่าน {bold(f'{passed}/{len(results)}')} ข้อ  ·  "
          f"Moulinette ผ่านถึง {bold(last)}")
    print(dim("  ตัวตรวจช่วยดูผลเท่านั้น ตอน evaluate ยังต้องให้เพื่อนอธิบายโค้ดตามใบประเมิน"))
    if web:
        path = write_report(proj, root, results, last)
        print(dim(f"  หน้าเว็บ: {path}"))
        open_report(path)
    if (fix or (fix is None and mine)) and sys.stdin.isatty():
        if offer_fixes(root, results):
            print(dim("  ตรวจซ้ำหลังแก้..."))
            return grade(proj, root, mine=mine, web=web, fix=False)
    return results


def main(argv):
    web = "--no-web" not in argv
    fix = True if "--fix" in argv else (False if "--peer" in argv else None)
    args = [a for a in argv if not a.startswith("--")]
    if not args:
        proj, root, mine = menu()
        return grade(proj, root, mine=mine, web=web, fix=fix)
    first = args[0].upper()
    if first == "UPDATE":
        return update()
    if first in ("HELP", "-H"):
        print(__doc__)
        return
    if first not in PROJECTS:
        print(red(f"  ไม่รู้จักโปรเจกต์ {args[0]}") + dim(f"  (มี: {' '.join(PROJECTS)})"))
        print(__doc__)
        sys.exit(1)
    target = args[1] if len(args) > 1 else "."
    mine = False
    if is_url(target):
        root = clone(target, first)
    else:
        root = os.path.abspath(os.path.expanduser(target))
        if not os.path.isdir(root):
            print(red(f"  ไม่เจอโฟลเดอร์ {root}"))
            sys.exit(1)
        login = os.environ.get("USER", "")
        mine = bool(login) and any(f"By: {login} " in read(os.path.join(dp, f))
                                   for dp, _, fs in os.walk(root) if ".git" not in dp for f in fs if f.endswith(".c"))
    grade(first, root, mine=mine, web=web, fix=fix)


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except KeyboardInterrupt:
        print()
