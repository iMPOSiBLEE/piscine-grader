# piscine-grader

ตัวตรวจ C Piscine 42 (C00–C09) พร้อมหน้าเว็บสรุปผล

## ติดตั้ง (ครั้งเดียว ไม่ต้องใช้ sudo)
```bash
git clone https://github.com/iMPOSiBLEE/piscine-grader.git ~/piscine-grader
bash ~/piscine-grader/install.sh
```
ปิด Terminal แล้วเปิดใหม่

## ใช้
```bash
grade C03 ~/eval_c03                       # ตรวจงานในโฟลเดอร์
grade C03 git@vogsphere.42bangkok.com:...  # clone งานเพื่อนให้เองแล้วตรวจ
grade C03 ~/eval_c03 --no-web              # ไม่เปิดหน้าเว็บ
grade update                               # อัปเดตตัวตรวจ
```
ผลขึ้นใน Terminal และเปิดหน้าเว็บสรุปให้อัตโนมัติ (เก็บไว้ที่ `~/grade_reports/`)

## เช็กอะไรบ้าง
- ไฟล์ครบไหม ชื่อ/โฟลเดอร์ถูกไหม มีไฟล์เกินไหม
- 42 header · norminette (C08 ใช้ `-R CheckDefine`) · คอมไพล์ `cc -Wall -Wextra -Werror`
- ฟังก์ชันต้องห้าม (ดูจากไฟล์ .o จริง) · ห้ามมี main (ยกเว้น C06)
- ผลลัพธ์หลายเคส รวมเคสขอบ · โปรแกรมค้างหรือ crash
- C09: รัน `sh libft_creator.sh` จริง และเทสต์ Makefile ทุก rule

ตัวตรวจช่วยดูผลเท่านั้น ตอน evaluate ยังต้องอ่านโค้ดกับเพื่อนตามใบประเมิน
