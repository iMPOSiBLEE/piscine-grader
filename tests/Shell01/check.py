"""ตัวตรวจ Shell01: check(ex, exdir, wd) -> list of cases"""
import getpass
import glob
import os
import re
import subprocess


def ok(name, cond, exp="", got=""):
    c = {"name": name, "ok": bool(cond)}
    if not cond:
        c.update(exp=str(exp), got=str(got))
    return c


def run(script, cwd, env=None):
    e = dict(os.environ, LC_ALL="C", **(env or {}))
    try:
        r = subprocess.run(["bash", script], cwd=cwd, env=e, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15)
        return r.stdout.decode("utf-8", "replace"), r.stderr.decode("utf-8", "replace")
    except subprocess.TimeoutExpired:
        return "", "TIMEOUT"


def vis(t):
    return t.replace("\n", "$\n") if t else "(ว่าง)"


def groups(user):
    try:
        r = subprocess.run(["id", "-Gn", user], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        return r.stdout.decode().split()
    except OSError:
        return []


def to_base(n, digits):
    b = len(digits)
    if n == 0:
        return digits[0]
    s = ""
    while n:
        s = digits[n % b] + s
        n //= b
    return s


def from_base(s, digits):
    n = 0
    for ch in s:
        n = n * len(digits) + digits.index(ch)
    return n


def make_tree(d):
    for f in ["a.sh", "b.txt", "sub/c.sh", "sub/d.c", "sub/deep/e.sh", "sub/deep/f.sh.bak", ".hidden.sh", "g.SH"]:
        p = os.path.join(d, f)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w").write("x")
    os.makedirs(os.path.join(d, "emptydir"), exist_ok=True)


def check(ex, exdir, wd):
    s = lambda name: os.path.join(exdir, name)
    if ex == "ex01":
        cases = []
        users = [getpass.getuser(), "root", "daemon"]
        for u in users:
            g = groups(u)
            if not g:
                continue
            exp = ",".join(g)
            got, err = run(s("print_groups.sh"), wd, {"FT_USER": u})
            cases.append(ok(f"FT_USER={u} (คั่นด้วย , ไม่มีช่องว่าง ไม่มีขึ้นบรรทัดใหม่)", got == exp, exp, vis(got) + err))
        return cases
    if ex in ("ex02", "ex03"):
        d = os.path.join(wd, "tree")
        make_tree(d)
        if ex == "ex02":
            exp = sorted(os.path.basename(p)[:-3] for p in glob.glob(d + "/**/*.sh", recursive=True) +
                         glob.glob(d + "/**/.*.sh", recursive=True))
            exp = sorted(set(exp) | {".hidden"})
            got, err = run(s("find_sh.sh"), d)
            g = sorted(l for l in got.split("\n") if l)
            return [ok("แสดงชื่อไฟล์ .sh ทั้งหมด (ไม่มี path ไม่มี .sh)", g == exp, ", ".join(exp), ", ".join(g) or err)]
        n = 0
        for root, dirs, files in os.walk(d):
            n += 1 + len(files)
        got, err = run(s("count_files.sh"), d)
        return [ok("นับไฟล์ + โฟลเดอร์ทั้งหมด (รวม .)", got.strip() == str(n), str(n), vis(got) + err)]
    if ex == "ex04":
        macs = set()
        for p in glob.glob("/sys/class/net/*/address"):
            macs.add(open(p).read().strip().lower())
        got, err = run(s("MAC.sh"), wd)
        lines = [l.strip().lower() for l in got.split("\n") if l.strip()]
        fmt = all(re.fullmatch(r"([0-9a-f]{2}:){5}[0-9a-f]{2}", l) for l in lines)
        return [ok("แสดง MAC address อย่างน้อย 1 ตัว", lines, "aa:bb:cc:dd:ee:ff", vis(got) + err),
                ok("ทุกบรรทัดเป็นรูปแบบ MAC (xx:xx:xx:xx:xx:xx)", fmt and lines, "xx:xx:xx:xx:xx:xx", vis(got)),
                ok("แต่ละบรรทัดตามด้วยขึ้นบรรทัดใหม่", got.endswith("\n"), "...$", vis(got)),
                ok("เป็น MAC ของเครื่องนี้จริง", not macs or set(lines) <= macs, ", ".join(sorted(macs)), ", ".join(lines))]
    if ex == "ex05":
        name = "\"\\?$*'MaRViN'*$?\\\""
        t = open(os.path.join(exdir, name), "rb").read()
        return [ok("มีแค่ \"42\" ไม่มีขึ้นบรรทัดใหม่", t == b"42", "42", repr(t))]
    if ex == "ex06":
        d = os.path.join(wd, "sk")
        make_tree(d)
        r = subprocess.run("ls -l", shell=True, cwd=d, stdout=subprocess.PIPE, env=dict(os.environ, LC_ALL="C"))
        exp = "".join(l + "\n" for i, l in enumerate(r.stdout.decode().split("\n")[:-1]) if i % 2 == 0)
        got, err = run(s("skip.sh"), d)
        return [ok("แสดงบรรทัดที่ 1, 3, 5, ... ของ ls -l", got == exp, vis(exp), vis(got) + err)]
    if ex == "ex07":
        rows = [l for l in open("/etc/passwd").read().split("\n") if l and not l.startswith("#")]
        logins = [l.split(":")[0][::-1] for i, l in enumerate(rows) if i % 2 == 1]
        logins.sort(reverse=True)
        cases = []
        for a, b in [(7, 15), (1, 3), (2, 2)]:
            exp = ", ".join(logins[a - 1:b]) + "."
            got, err = run(s("r_dwssap.sh"), wd, {"FT_LINE1": str(a), "FT_LINE2": str(b)})
            cases.append(ok(f"FT_LINE1={a} FT_LINE2={b}", got.rstrip("\n") == exp and not got.endswith("\n\n"),
                            exp, vis(got) + err))
        return cases
    if ex == "ex08":
        b1, b2, b3 = "'\\\"?!", "mrdoc", "gtaio luSnemf"
        cases = []
        for n1, n2 in [("\\'?\"\\\"'\\", "rcrdmddd"), ("\\\"\\\"!\\\"\\\"!\\\"\\\"!\\\"\\\"!\\\"\\\"!\\\"\\\"", "dcrcmcmooododmrrrmorcmcrmomo"),
                       ("!", "r"), ("'", "m")]:
            exp = to_base(from_base(n1, b1) + from_base(n2, b2), b3)
            got, err = run(s("add_chelou.sh"), wd, {"FT_NBR1": n1, "FT_NBR2": n2})
            cases.append(ok(f"FT_NBR1={n1} FT_NBR2={n2} → {exp}", got.rstrip("\n") == exp, exp, vis(got) + err))
        return cases
    return []
