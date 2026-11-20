#!/bin/bash
# ติดตั้งคำสั่ง grade / grader (ไม่ต้องใช้ sudo)
HERE="$(cd "$(dirname "$0")" && pwd)"
for rc in "$HOME/.zshrc" "$HOME/.bashrc"; do
	touch "$rc"
	grep -v -E "alias grade(r)?=" "$rc" > "$rc.tmp_grade" && cat "$rc.tmp_grade" > "$rc" && rm -f "$rc.tmp_grade"
	echo "alias grade='bash \"$HERE/grade.sh\"'" >> "$rc"
	echo "alias grader='bash \"$HERE/grade.sh\"'" >> "$rc"
done
echo "ติดตั้งแล้ว ✓  ปิด Terminal แล้วเปิดใหม่ จากนั้นพิมพ์:  grade"
