"""ตัวตรวจ Shell00: check(ex, exdir, wd) -> list of cases"""
import os
import re
import subprocess
import tarfile
import time


def ok(name, cond, exp="", got=""):
    c = {"name": name, "ok": bool(cond)}
    if not cond:
        c.update(exp=str(exp), got=str(got))
    return c


def sh(cmd, cwd, env=None, inp=None, timeout=15):
    e = dict(os.environ, LC_ALL="C", **(env or {}))
    try:
        r = subprocess.run(cmd, cwd=cwd, env=e, input=inp, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           timeout=timeout, shell=isinstance(cmd, str))
        return r.stdout.decode("utf-8", "replace"), r.stderr.decode("utf-8", "replace"), r.returncode
    except subprocess.TimeoutExpired:
        return "", "TIMEOUT", -1


def mode_str(m, kind):
    s = {"d": "d", "l": "l", "f": "-"}[kind]
    for i, ch in enumerate("rwxrwxrwx"):
        s += ch if m & (1 << (8 - i)) else "-"
    return s


def when(mtime):
    t = time.localtime(mtime)
    return t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min


def check_entry(name, info, kind, mode, size, mon, day, hh, mm, link=None):
    cases = []
    k = "d" if info.isdir() else "l" if info.issym() else "f"
    cases.append(ok(f"{name}: ชนิด", k == kind, kind, k))
    cases.append(ok(f"{name}: สิทธิ์", mode_str(info.mode, k) == mode, mode, mode_str(info.mode, k)))
    if size is not None and k == "f":
        cases.append(ok(f"{name}: ขนาด {size} ไบต์", info.size == size, size, info.size))
    m, d, h, mi = when(info.mtime)
    t_ok = (m, d) == (mon, day) and ((h, mi) == (hh, mm) or True)
    cases.append(ok(f"{name}: วันที่ Jun {day} {hh:02d}:{mm:02d}", (m, d, h, mi) == (mon, day, hh, mm),
                    f"Jun {day} {hh:02d}:{mm:02d}", time.strftime("%b %d %H:%M", time.localtime(info.mtime))))
    if link:
        cases.append(ok(f"{name}: ชี้ไปที่ {link}", info.linkname == link, link, info.linkname))
    return cases


def check(ex, exdir, wd):
    if ex == "ex00":
        out, _, _ = sh(["cat", "z"], exdir)
        return [ok("cat z ต้องได้ 'Z' ตามด้วยขึ้นบรรทัดใหม่", out == "Z\n", "Z$", out.replace("\n", "$"))]
    if ex == "ex01":
        try:
            tf = tarfile.open(os.path.join(exdir, "testShell00.tar"))
            mem = {m.name.lstrip("./"): m for m in tf.getmembers()}
        except (tarfile.TarError, OSError) as e:
            return [ok("เปิด testShell00.tar ได้", False, "ไฟล์ tar", str(e))]
        if "testShell00" not in mem:
            return [ok("ใน tar มีไฟล์ testShell00", False, "testShell00", ", ".join(mem))]
        return check_entry("testShell00", mem["testShell00"], "f", "-r--r-xr-x", 40, 6, 1, 23, 42)
    if ex == "ex02":
        try:
            tf = tarfile.open(os.path.join(exdir, "exo2.tar"))
            mem = {m.name.lstrip("./").rstrip("/"): m for m in tf.getmembers()}
        except (tarfile.TarError, OSError) as e:
            return [ok("เปิด exo2.tar ได้", False, "ไฟล์ tar", str(e))]
        cases = []
        want = [("test0", "d", "drwx--xr-x", None, 20, 47), ("test1", "f", "-rwx--xr--", 4, 21, 46),
                ("test2", "d", "dr-x---r--", None, 22, 45), ("test3", "f", "-r-----r--", 1, 23, 44),
                ("test4", "f", "-rw-r----x", 2, 23, 43), ("test5", "f", "-r-----r--", 1, 23, 44),
                ("test6", "l", "lrwxrwxrwx", None, 22, 20)]
        for name, kind, mode, size, hh, mm in want:
            if name not in mem:
                cases.append(ok(f"ใน tar มี {name}", False, name, "ไม่มี"))
                continue
            info = mem[name]
            if info.islnk():   # hard link: ข้อมูลอยู่ที่ไฟล์ต้นทาง
                src = mem.get(info.linkname.lstrip("./"))
                cases.append(ok(f"{name}: เป็น hard link กับ test3/test5", info.linkname.lstrip("./") in ("test3", "test5"),
                                "test3 ↔ test5", info.linkname))
                if src:
                    info = src
            cases += check_entry(name, info, kind, mode, size, 6, 1, hh, mm, "test0" if name == "test6" else None)
        has_link = any(m.islnk() for m in mem.values())
        cases.append(ok("test3 กับ test5 เป็น hard link (ls -l ขึ้นเลข 2)", has_link, "hard link", "ไม่มี"))
        return cases
    if ex == "ex03":
        t = open(os.path.join(exdir, "id_rsa_pub"), errors="replace").read()
        return [ok("เป็น public key (ขึ้นต้นด้วย ssh-...)", re.match(r"^(ssh-|ecdsa-)", t.strip()), "ssh-rsa AAAA...", t[:40]),
                ok("ไม่ใช่ private key (ห้ามส่ง private key!)", "PRIVATE" not in t, "public key", "PRIVATE KEY")]
    if ex == "ex04":
        d = os.path.join(wd, "ls_test")
        os.makedirs(d)
        for i, n in enumerate(["old_file", "dirA", "mid_file", "dirB", ".hidden", "new_file", "zz"]):
            p = os.path.join(d, n)
            if n.startswith("dir"):
                os.makedirs(p)
            else:
                open(p, "w").close()
            os.utime(p, (1_600_000_000 + i * 100, 1_600_000_000 + i * 100))
        script = os.path.join(exdir, "midLS")
        got, err, _ = sh(["sh", script], d)
        exp, _, _ = sh(["ls", "-m", "-t", "-p"], d)
        return [ok("รัน midLS ในโฟลเดอร์ทดสอบ (เรียงตามเวลา, คั่นด้วย , , โฟลเดอร์มี /)", got == exp,
                   exp.replace("\n", "$"), (got + err).replace("\n", "$"))]
    if ex in ("ex05", "ex06"):
        d = os.path.join(wd, "repo")
        os.makedirs(d)
        env = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
               "HOME": wd}
        sh("git init -q .", d, env)
        if ex == "ex05":
            for i in range(7):
                open(os.path.join(d, f"f{i}"), "w").write(str(i))
                sh(f"git add . && git commit -q -m c{i}", d, env)
            exp, _, _ = sh("git log -5 --format=%H", d, env)
            got, err, _ = sh(["bash", os.path.join(exdir, "git_commit.sh")], d, env)
            return [ok("แสดง id ของ 5 commit ล่าสุด บรรทัดละ 1 id", got == exp, exp.replace("\n", "$"),
                       (got + err).replace("\n", "$"))]
        open(os.path.join(d, ".gitignore"), "w").write("*.o\n*~\n.DS_Store\nbuild/\n")
        for f in ["keep.c", "a.o", "x~", ".DS_Store", "build/out.txt", "sub/y.o", "sub/keep.h"]:
            p = os.path.join(d, f)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            open(p, "w").write("x")
        sh("git add .gitignore keep.c sub/keep.h && git commit -q -m init", d, env)
        exp, _, _ = sh("git ls-files --others --ignored --exclude-standard", d, env)
        got, err, _ = sh(["bash", os.path.join(exdir, "git_ignore.sh")], d, env)
        norm = lambda t: sorted(l.strip().lstrip("./") for l in t.split("\n") if l.strip())
        return [ok("แสดงไฟล์ที่ถูก ignore ทั้งหมด", norm(got) == norm(exp), ", ".join(norm(exp)), ", ".join(norm(got)) or err)]
    if ex == "ex07":
        t = open(os.path.join(exdir, "b"), errors="replace").read()
        return [ok("มีไฟล์ b และมีเนื้อหา (ต้องเทียบ diff a b กับ sw.diff เอง)", t.strip(), "มีเนื้อหา", "ว่าง")]
    if ex == "ex08":
        cmd = open(os.path.join(exdir, "clean"), errors="replace").read()
        lines = [l for l in cmd.split("\n") if l.strip() and not l.strip().startswith("#")]
        single = len(lines) == 1 and not re.search(r";|&&|\|\|", lines[0] if lines else "")
        d = os.path.join(wd, "cl")
        files = ["a~", "#b#", "keep.c", "sub/d~", "sub/#e#", "#f", "g#", "h~x", "sub/deep/i~"]
        for f in files:
            p = os.path.join(d, f)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            open(p, "w").close()
        got, err, _ = sh(["sh", os.path.join(exdir, "clean")], d)
        should_go = {"a~", "#b#", "sub/d~", "sub/#e#", "sub/deep/i~"}
        left = {f for f in files if os.path.exists(os.path.join(d, f))}
        shown = {l.strip().lstrip("./") for l in got.split("\n") if l.strip()}
        return [ok("มีคำสั่งเดียว (ห้ามมี ; && ||)", single, "1 คำสั่ง", cmd.strip()[:120]),
                ok("ลบไฟล์ที่ลงท้ายด้วย ~ หรือขึ้นต้นและลงท้ายด้วย # ครบ", not (left & should_go),
                   "ลบ: " + ", ".join(sorted(should_go)), "ยังเหลือ: " + ", ".join(sorted(left & should_go))),
                ok("ไม่ลบไฟล์อื่น", left == set(files) - should_go, ", ".join(sorted(set(files) - should_go)),
                   ", ".join(sorted(left))),
                ok("แสดงชื่อไฟล์ที่ลบ", shown == should_go, ", ".join(sorted(should_go)), ", ".join(sorted(shown)) or err)]
    if ex == "ex09":
        yes, no = os.path.join(wd, "is42"), os.path.join(wd, "not42")
        open(yes, "wb").write(b"x" * 41 + b"42" + b"y" * 20)
        open(no, "wb").write(b"x" * 63)
        mg = os.path.join(exdir, "ft_magic")
        g1, e1, _ = sh(["file", "-m", mg, yes], wd)
        g2, _, _ = sh(["file", "-m", mg, no], wd)
        return [ok("file -m ft_magic รู้จักไฟล์ที่มี 42 ที่ไบต์ที่ 42", "42" in g1.split(":", 1)[-1], "...42 file", g1 or e1),
                ok("ไฟล์ที่ไม่มี 42 ต้องไม่ถูกจับ", "42" not in g2.split(":", 1)[-1], "data", g2)]
    return []
