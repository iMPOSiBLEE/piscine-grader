#!/bin/bash
# piscine-grader: ตัวตรวจ C Piscine C00–C09
# ใช้: grade <C00..C09> <โฟลเดอร์งาน หรือ ลิงก์ git ของเพื่อน> [--no-web]

HERE="$(cd "$(dirname "$0")/.." && pwd)"
TIMEOUT="${TIMEOUT:-10}"
G=$'\033[32m'; R=$'\033[31m'; Y=$'\033[33m'; B=$'\033[1m'; D=$'\033[2m'; N=$'\033[0m'

WEB=1
ARGS=()
for a in "$@"; do
	case "$a" in
		--no-web) WEB=0 ;;
		*) ARGS+=("$a") ;;
	esac
done
PROJ="$(echo "${ARGS[0]}" | tr '[:lower:]' '[:upper:]')"
DIR="${ARGS[1]:-.}"

usage() {
	echo "${B}วิธีใช้${N}"
	echo "  grade C03 ~/eval_c03                 ตรวจงานในโฟลเดอร์"
	echo "  grade C03 git@vogsphere...            clone งานเพื่อนให้เองแล้วตรวจ"
	echo "  grade C03 ~/eval_c03 --no-web         ไม่ต้องเปิดหน้าเว็บ"
	echo "  grade update                          อัปเดตตัวตรวจเป็นเวอร์ชันล่าสุด"
	echo
	echo "โปรเจกต์ที่ตรวจได้: $(ls "$HERE/tests" | tr '\n' ' ')"
}

if [ "$PROJ" = "UPDATE" ]; then
	git -C "$HERE" pull --ff-only && echo "${G}อัปเดตแล้ว${N}"
	exit $?
fi
if [ -z "$PROJ" ] || [ "$PROJ" = "HELP" ] || [ ! -f "$HERE/tests/$PROJ/files.txt" ]; then
	[ -n "$PROJ" ] && [ "$PROJ" != "HELP" ] && echo "${R}ไม่รู้จักโปรเจกต์ ${ARGS[0]}${N}" && echo
	usage
	exit 1
fi

# ถ้าให้ลิงก์ git มา ให้ clone เอง
case "$DIR" in
	*@*:*|http://*|https://*|*.git)
		DEST="$HOME/grade_eval/${PROJ}_$(date +%m%d_%H%M%S)"
		mkdir -p "$HOME/grade_eval"
		echo "${D}กำลัง clone งานเพื่อนไปที่ $DEST ...${N}"
		if ! git clone -q "$DIR" "$DEST"; then
			echo "${R}clone ไม่สำเร็จ เช็กลิงก์อีกที (หรือเครื่องนี้ยังไม่ได้ตั้ง SSH key กับ intra)${N}"
			exit 1
		fi
		DIR="$DEST"
		;;
esac
if [ ! -d "$DIR" ]; then echo "${R}ไม่เจอโฟลเดอร์ $DIR${N}"; exit 1; fi
DIR="$(cd "$DIR" && pwd)"
TESTS="$HERE/tests/$PROJ"
COMMON="$HERE/tests/common"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
CFLAGS="-Wall -Wextra -Werror"

HAS_NORM=1
command -v norminette >/dev/null 2>&1 || HAS_NORM=0

# รันแบบมีเวลาจำกัด (ใช้ perl เพราะ Mac ไม่มีคำสั่ง timeout)
run_limited() { perl -e 'alarm shift; exec @ARGV' "$TIMEOUT" "$@"; }

ok()   { echo "  ${G}✔${N} $*"; }
bad()  { echo "  ${R}✘ $*${N}"; }
warn() { echo "  ${Y}⚠ $*${N}"; }
indent() { sed 's/^/      /' | head -n "${1:-12}"; }

# แปลผล exit code ของโปรแกรมเทสต์
result_of() {
	case "$1" in
		0) echo OK ;;
		1) echo KO ;;
		142) bad "ช้าเกิน ${TIMEOUT} วินาที (ค้าง/วนไม่จบ)" >&2; echo TIMEOUT ;;
		*) bad "โปรแกรมพัง (crash, code $1)" >&2; echo CRASH ;;
	esac
}

check_header() { # $1 file
	if head -n 12 "$1" | grep -q "By:" && head -n 12 "$1" | grep -q "Created:"; then
		ok "$(basename "$1"): มี 42 header"
	else
		bad "$(basename "$1"): ไม่มี 42 header"; PROBLEMS="$PROBLEMS header"
	fi
}

check_main() { # $1 file
	if grep -Eq '(^|[^_[:alnum:]])main[[:space:]]*\(' "$1"; then
		bad "$(basename "$1"): มีฟังก์ชัน main (ห้ามมีในข้อนี้)"; PROBLEMS="$PROBLEMS main"
	fi
}

check_norm() { # files...
	[ $HAS_NORM -eq 0 ] && return
	local flags="-R CheckForbiddenSourceHeader"
	[ "$PROJ" = "C08" ] && flags="-R CheckDefine"
	local out
	out="$(norminette $flags "$@" 2>&1)"
	if echo "$out" | grep -q "Error"; then
		bad "norminette ไม่ผ่าน"; echo "$out" | grep -v "OK!" | indent 14
		PROBLEMS="$PROBLEMS norm"
	else
		ok "norminette ผ่าน"
	fi
}

# compile .c ของเพื่อนทีละไฟล์ด้วย flag จริง แล้วเช็กฟังก์ชันต้องห้าม
compile_peer() { # $1 exdir, $2 allowed, files...
	local exdir="$1" allowed="$2"; shift 2
	local f objs="" defined="" undef=""
	for f in "$@"; do
		local o="$WORK/$(basename "$f" .c).o"
		if ! cc $CFLAGS -I"$exdir" -I"$TESTS/include" -c "$f" -o "$o" 2>"$WORK/cc.txt"; then
			bad "$(basename "$f"): คอมไพล์ไม่ผ่าน (cc $CFLAGS)"; indent < "$WORK/cc.txt"
			return 1
		fi
		objs="$objs $o"
	done
	defined="$(nm $objs 2>/dev/null | awk 'NF>=2 && $(NF-1)!="U" {print $NF}' | sed 's/^_*//')"
	undef="$(nm $objs 2>/dev/null | awk 'NF>=2 && $(NF-1)=="U" {print $NF}' | sed 's/^_*//' | sort -u)"
	local BAD="" s
	for s in $undef; do
		echo "$defined" | grep -qx "$s" && continue
		echo ",$allowed," | grep -q ",$s," && continue
		# ข้ามสัญลักษณ์ที่คอมไพเลอร์ใส่เองตอน copy/ล้าง array (ถ้าไม่ได้เขียนเรียกเองในโค้ด)
		case "$s" in
			stack_chk_fail|stack_chk_guard|dyld_stub_binder|"") continue ;;
			memset|memcpy|memmove|bzero|*memset_chk|*memcpy_chk|*memmove_chk)
				cat "$@" | grep -Eq "(^|[^_[:alnum:]])$s[[:space:]]*\(" || continue ;;
		esac
		BAD="$BAD $s"
	done
	if [ -n "$BAD" ]; then
		bad "ใช้ฟังก์ชันต้องห้าม:$BAD  ${D}(อนุญาต: ${allowed:-ไม่มี})${N}"; PROBLEMS="$PROBLEMS forbidden"
		echo "$BAD" | grep -qE "puts|putchar|printf" && echo "      ${D}(printf จะถูกคอมไพเลอร์แปลงเป็น puts/putchar ได้ ให้ดูโค้ดว่าใช้ printf ไหม)${N}"
	else
		ok "ไม่ใช้ฟังก์ชันต้องห้าม  ${D}(อนุญาต: ${allowed:-ไม่มี})${N}"
	fi
	return 0
}

run_func() { # EX exdir allowed files...
	local ex="$1" exdir="$2" allowed="$3"; shift 3
	local f
	for f in "$@"; do check_main "$f"; done
	compile_peer "$exdir" "$allowed" "$@" || { RES="คอมไพล์ไม่ผ่าน"; return; }
	# ลิงก์กับตัวเทสต์ (ถ้ามี main แอบเปลี่ยนชื่อทิ้งเพื่อให้ยังเทสต์ต่อได้)
	local objs=""
	for f in "$@"; do
		cc -w -Dmain=peer_main_not_allowed -I"$exdir" -I"$TESTS/include" -c "$f" -o "$WORK/t_$(basename "$f" .c).o" 2>/dev/null
		objs="$objs $WORK/t_$(basename "$f" .c).o"
	done
	if ! cc -w -I"$HERE/lib" -I"$exdir" -I"$TESTS/include" "$TESTS/$ex.c" $objs -o "$WORK/t" 2>"$WORK/cc2.txt"; then
		bad "ใช้กับตัวเทสต์ไม่ได้ (ชื่อฟังก์ชันหรือ prototype ไม่ตรงโจทย์?)"; indent 8 < "$WORK/cc2.txt"
		RES="ใช้กับตัวเทสต์ไม่ได้"; return
	fi
	( run_limited "$WORK/t" ) 2>/dev/null
	RES="$(result_of $?)"
}

run_header() { # EX exdir files...
	local ex="$1" exdir="$2"
	if ! cc $CFLAGS -Wno-unused-function -I"$HERE/lib" -I"$exdir" "$TESTS/$ex.c" -o "$WORK/t" 2>"$WORK/cc2.txt"; then
		bad "คอมไพล์ไม่ผ่านเมื่อใช้ header นี้ (cc $CFLAGS)"; indent 10 < "$WORK/cc2.txt"
		RES="คอมไพล์ไม่ผ่าน"; return
	fi
	( run_limited "$WORK/t" ) 2>/dev/null
	RES="$(result_of $?)"
}

run_prog() { # EX exdir allowed file
	local ex="$1" exdir="$2" allowed="$3" f="$4"
	compile_peer "$exdir" "$allowed" "$f" || { RES="คอมไพล์ไม่ผ่าน"; return; }
	mkdir -p "$WORK/p" "$WORK/r"
	cc $CFLAGS "$f" -o "$WORK/p/a.out" 2>/dev/null || { bad "ลิงก์เป็นโปรแกรมไม่ได้ (ไม่มี main?)"; RES="ไม่มี main"; return; }
	cc -w "$TESTS/ref_$ex.c" -o "$WORK/r/a.out"
	local fails=0 total=0 set
	while IFS= read -r set; do
		total=$((total + 1))
		eval "args=($set)"
		(cd "$WORK/r" && ./a.out "${args[@]}") > "$WORK/exp.txt" 2>/dev/null
		(cd "$WORK/p" && run_limited ./a.out "${args[@]}") > "$WORK/got.txt" 2>/dev/null
		local code=$?
		if [ $code -ne 0 ] && [ $code -ne 1 ]; then
			bad "./a.out $set  →  พัง/ค้าง (code $code)"; fails=$((fails + 1))
		elif cmp -s "$WORK/exp.txt" "$WORK/got.txt"; then
			ok "./a.out $set"
		else
			bad "./a.out $set"
			echo "      ควรได้ (cat -e):"; cat -e "$WORK/exp.txt" | indent 6
			echo "      ได้จริง (cat -e):"; cat -e "$WORK/got.txt" | indent 6
			fails=$((fails + 1))
		fi
	done < "$TESTS/args.txt"
	echo "  ── $((total - fails))/$total เคสผ่าน"
	[ $fails -eq 0 ] && RES=OK || RES=KO
}

run_script() { # C09 ex00: libft_creator.sh
	local exdir="$1" f
	for f in "$exdir"/*.c; do [ -f "$f" ] && check_main "$f"; done
	compile_peer "$exdir" "write" "$exdir"/ft_*.c || { RES="คอมไพล์ไม่ผ่าน"; return; }
	rm -rf "$WORK/s" && mkdir -p "$WORK/s" && cp "$exdir"/* "$WORK/s/"
	(cd "$WORK/s" && run_limited sh libft_creator.sh) > "$WORK/sh.txt" 2>&1
	if [ ! -f "$WORK/s/libft.a" ]; then
		bad "รัน sh libft_creator.sh แล้วไม่ได้ไฟล์ libft.a"; indent < "$WORK/sh.txt"; RES="ไม่ได้ libft.a"; return
	fi
	ok "sh libft_creator.sh สร้าง libft.a ได้"
	if ! cc -w -I"$HERE/lib" "$TESTS/ex00.c" -L"$WORK/s" -lft -o "$WORK/t" 2>"$WORK/cc2.txt"; then
		bad "ลิงก์กับ libft.a ไม่ได้ (ฟังก์ชันไม่ครบ 5 ตัว?)"; indent < "$WORK/cc2.txt"; RES="libft.a ไม่ครบ"; return
	fi
	( run_limited "$WORK/t" ) 2>/dev/null
	RES="$(result_of $?)"
}

run_make() { # C09 ex01: Makefile
	local exdir="$1" m="$WORK/m" fails=0
	rm -rf "$m" && mkdir -p "$m" && cp "$exdir/Makefile" "$m/" && cp -R "$TESTS/libft_srcs/srcs" "$TESTS/libft_srcs/includes" "$m/"
	t() { if eval "$2"; then ok "$1"; else bad "$1"; fails=$((fails + 1)); fi; }
	(cd "$m" && run_limited make) > "$WORK/mk1.txt" 2>&1
	t "make สร้าง libft.a" '[ -f "$m/libft.a" ]'
	t "make แสดงคำสั่งที่รัน (มีบรรทัด cc ... -Wall -Wextra -Werror)" 'grep -q "cc.*-Wall" "$WORK/mk1.txt" && grep -q -- "-Wextra" "$WORK/mk1.txt" && grep -q -- "-Werror" "$WORK/mk1.txt"'
	t "ไฟล์ .o อยู่ข้าง .c ใน srcs/" '[ -f "$m/srcs/ft_putchar.o" ] && [ -f "$m/srcs/ft_strcmp.o" ]'
	t "libft.a มีครบ 5 ฟังก์ชัน" 'n=$(nm "$m/libft.a" 2>/dev/null | grep -cE " T _?ft_(putchar|swap|putstr|strlen|strcmp)$"); [ "$n" -eq 5 ]'
	(cd "$m" && run_limited make) > "$WORK/mk2.txt" 2>&1
	t "รัน make ซ้ำ ไม่คอมไพล์อะไรใหม่" '! grep -qE "(^|[[:space:]])(cc|ar) " "$WORK/mk2.txt"'
	(cd "$m" && run_limited make clean) > /dev/null 2>&1
	t "make clean ลบ .o แต่ libft.a ยังอยู่" '! ls "$m"/srcs/*.o >/dev/null 2>&1 && [ -f "$m/libft.a" ]'
	(cd "$m" && run_limited make fclean) > /dev/null 2>&1
	t "make fclean ลบ libft.a ด้วย" '[ ! -f "$m/libft.a" ] && ! ls "$m"/srcs/*.o >/dev/null 2>&1'
	(cd "$m" && run_limited make re) > /dev/null 2>&1
	t "make re สร้างใหม่ได้" '[ -f "$m/libft.a" ]'
	(cd "$m" && make fclean >/dev/null 2>&1; run_limited make libft.a) > /dev/null 2>&1
	t "make libft.a ใช้ได้" '[ -f "$m/libft.a" ]'
	[ $fails -eq 0 ] && RES=OK || RES=KO
}

echo
echo "${B}═══ ตรวจ $PROJ ═══${N}  ${D}$DIR${N}"
[ $HAS_NORM -eq 0 ] && echo "${Y}⚠ ไม่เจอ norminette ในเครื่องนี้ ข้ามการเช็ก norm${N}"

EXPECTED_DIRS="$(awk '{print $1}' "$TESTS/files.txt")"
for d in "$DIR"/*; do
	[ -e "$d" ] || continue
	echo "$EXPECTED_DIRS" | grep -qx "$(basename "$d")" || echo "${Y}⚠ มีของเกินในโฟลเดอร์งาน: $(basename "$d")${N}"
done

STREAK=1
LAST_OK="ไม่มี"
SUMMARY=""

grade_ex() {
	EXDIR="$DIR/$EX"
	PROBLEMS=""
	RES=""

	MISSING=""
	PATHS=()
	for f in $(echo "$FILES" | tr ',' ' '); do
		[ -f "$EXDIR/$f" ] || MISSING="$MISSING $f"
		PATHS+=("$EXDIR/$f")
	done
	if [ -d "$EXDIR" ]; then
		for f in "$EXDIR"/* "$EXDIR"/.[!.]*; do
			[ -e "$f" ] || continue
			b="$(basename "$f")"
			[ "$b" = ".DS_Store" ] && continue
			echo ",$FILES," | grep -q ",$b," || warn "ไฟล์เกินใน $EX: $b (ห้ามมีไฟล์อื่นนอกจากที่โจทย์สั่ง)"
		done
	fi

	if [ -n "$MISSING" ]; then
		bad "ไม่มีไฟล์:$MISSING"
		RES="ไม่มีไฟล์"
	else
		for f in "${PATHS[@]}"; do check_header "$f"; done
		NORMFILES=()
		for f in "${PATHS[@]}"; do case "$f" in *.c|*.h) NORMFILES+=("$f");; esac; done
		[ ${#NORMFILES[@]} -gt 0 ] && check_norm "${NORMFILES[@]}"
		case "$TYPE" in
			func)   run_func "$EX" "$EXDIR" "$ALLOWED" "${PATHS[@]}" ;;
			header) run_header "$EX" "$EXDIR" ;;
			prog)   run_prog "$EX" "$EXDIR" "$ALLOWED" "${PATHS[0]}" ;;
			script) run_script "$EXDIR" ;;
			make)   run_make "$EXDIR" ;;
		esac
		[ "$RES" = "OK" ] && [ -n "$PROBLEMS" ] && RES="ผิดกฎ:$PROBLEMS"
	fi

}

while read -r EX TYPE FILES ALLOWED; do
	[ -z "$EX" ] && continue
	[ "$ALLOWED" = "-" ] && ALLOWED=""
	echo
	echo "${B}▶ $EX  ${D}($FILES)${N}"
	grade_ex > "$WORK/log_$EX.txt" 2>&1 < /dev/null
	cat "$WORK/log_$EX.txt"
	printf "%s\t%s\t%s\n" "$EX" "$RES" "$FILES" >> "$WORK/results.tsv"
	if [ "$RES" = "OK" ]; then
		echo "  ${G}${B}➜ $EX ผ่าน${N}"
		SUMMARY="$SUMMARY\n  ${G}✔ $EX${N}  $FILES"
		[ $STREAK -eq 1 ] && LAST_OK="$EX"
	else
		echo "  ${R}${B}➜ $EX ไม่ผ่าน ($RES)${N}"
		SUMMARY="$SUMMARY\n  ${R}✘ $EX${N}  $FILES  ${D}($RES)${N}"
		STREAK=0
	fi
done < "$TESTS/files.txt"

echo
echo "${B}═══ สรุป $PROJ ═══${N}"
printf "%b\n" "$SUMMARY"
echo
echo "${B}แบบ Moulinette (นับต่อเนื่องจาก ex00 หยุดที่ข้อแรกที่พัง): ผ่านถึง ${LAST_OK}${N}"
echo "${D}ตัวตรวจนี้ช่วยดูผลเท่านั้น ตอน evaluate ยังต้องอ่านโค้ดกับเพื่อนและให้เขาอธิบายตามใบประเมิน${N}"
echo

if [ $WEB -eq 1 ]; then
	if command -v python3 >/dev/null 2>&1; then
		mkdir -p "$HOME/grade_reports"
		OUT="$HOME/grade_reports/${PROJ}_$(basename "$DIR")_$(date +%m%d_%H%M%S).html"
		if python3 "$HERE/lib/report.py" "$PROJ" "$DIR" "$WORK" "$LAST_OK" > "$OUT"; then
			echo "${D}รายงานหน้าเว็บ: $OUT${N}"
			if command -v open >/dev/null 2>&1 && [ "$(uname)" = "Darwin" ]; then open "$OUT"
			elif command -v xdg-open >/dev/null 2>&1; then xdg-open "$OUT" >/dev/null 2>&1 &
			fi
		fi
	else
		echo "${Y}ไม่เจอ python3 เลยสร้างหน้าเว็บไม่ได้ (ผลใน Terminal ด้านบนใช้ได้ตามปกติ)${N}"
	fi
fi
