#include "ft_stock_str.h"
#include "t.h"
struct s_stock_str	*ft_strs_to_tab(int ac, char **av);
int	main(void)
{
	char a0[] = "Hello", a1[] = "", a2[] = "42 Bangkok";
	char *av[] = {a0, a1, a2};
	t_stock_str *t = ft_strs_to_tab(3, av);
	if (!t) { t_ko("ft_strs_to_tab(3, av)", "array", "NULL"); return (t_done()); }
	for (int i = 0; i < 3; i++)
	{
		char name[80];
		snprintf(name, 80, "[%d].size", i); t_int(name, t[i].size, strlen(av[i]));
		snprintf(name, 80, "[%d].str ต้องชี้ไปที่ av[%d] เดิม", i, i); t_ptr(name, t[i].str, av[i]);
		snprintf(name, 80, "[%d].copy เนื้อหาเหมือนกัน", i); t_str(name, t[i].copy, av[i]);
		snprintf(name, 80, "[%d].copy ต้องเป็นที่ใหม่ (malloc)", i);
		if (t[i].copy == av[i]) t_ko(name, "pointer ใหม่", "pointer เดียวกับ av"); else t_ok(name);
	}
	t_ptr("[3].str ต้องเป็น 0 (ปิดท้าย array)", t[3].str, NULL);
	a0[0] = 'X';
	t_str("แก้ av[0] แล้ว copy ต้องไม่เปลี่ยน", t[0].copy, "Hello");
	t_stock_str *z = ft_strs_to_tab(0, av);
	if (z) t_ptr("ft_strs_to_tab(0, av) → [0].str ต้องเป็น 0", z[0].str, NULL); else t_ok("ft_strs_to_tab(0, av) คืน NULL หรือ array ว่าง");
	return (t_done());
}
