#!/bin/bash
# piscine-grader: เรียกตัวตรวจหลัก (Python)
HERE="$(cd "$(dirname "$0")" && pwd)"
if ! command -v python3 >/dev/null 2>&1; then
	echo "ไม่เจอ python3 ใช้ตัวตรวจแบบเก่าแทน"
	exec bash "$HERE/lib/grade_legacy.sh" "$@"
fi
exec python3 "$HERE/grader.py" "$@"
