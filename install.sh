#!/bin/bash
# ติดตั้งคำสั่ง grade (ไม่ต้องใช้ sudo)
HERE="$(cd "$(dirname "$0")" && pwd)"
LINE="alias grade='bash \"$HERE/grade.sh\"'"
for rc in "$HOME/.zshrc" "$HOME/.bashrc"; do
	touch "$rc"
	grep -v "alias grade=" "$rc" > "$rc.tmp_grade" && cat "$rc.tmp_grade" > "$rc" && rm -f "$rc.tmp_grade"
	echo "$LINE" >> "$rc"
done
echo "ติดตั้งแล้ว ✓  ปิด Terminal แล้วเปิดใหม่ จากนั้นพิมพ์:  grade C03 ~/งานเพื่อน"
