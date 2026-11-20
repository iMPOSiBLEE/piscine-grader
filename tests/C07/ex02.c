#include "t.h"
int	ft_ultimate_range(int **range, int min, int max);
static void	c(int mn, int mx)
{
	char name[64]; int *t = (int *)1; int n = ft_ultimate_range(&t, mn, mx);
	snprintf(name, 64, "ft_ultimate_range(&r, %d, %d) ค่าที่ return", mn, mx);
	if (mn >= mx) { t_int(name, n, 0); t_ptr("  r ต้องเป็น NULL", t, NULL); return; }
	t_int(name, n, mx - mn);
	if (!t || t == (int *)1) { t_ko("  r ต้องชี้ไปที่ array", "array", "NULL/ไม่ได้ตั้งค่า"); return; }
	for (int i = 0; i < mx - mn; i++) if (t[i] != mn + i) { t_ko("  ค่าใน r", "เรียง min..max-1", "ไม่ตรง"); free(t); return; }
	t_ok("  ค่าใน r ถูก"); free(t);
}
int	main(void){ c(0, 5); c(-3, 3); c(7, 8); c(4, 4); c(9, 1); return (t_done()); }
