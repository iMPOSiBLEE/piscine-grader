#include "t.h"
void	ft_foreach(int *tab, int length, void (*f)(int));
static char	g_buf[256]; static int g_n;
static void	rec(int x){ g_n += sprintf(g_buf + g_n, "%d,", x); }
int	main(void)
{
	int t[] = {5, -3, 0, 42, 7};
	g_n = 0; g_buf[0] = 0; ft_foreach(t, 5, &rec); t_str("ft_foreach(tab, 5, f) เรียก f ตามลำดับ", g_buf, "5,-3,0,42,7,");
	g_n = 0; g_buf[0] = 0; ft_foreach(t, 2, &rec); t_str("ft_foreach(tab, 2, f) เรียกแค่ 2 ตัว", g_buf, "5,-3,");
	g_n = 0; g_buf[0] = 0; ft_foreach(t, 0, &rec); t_str("ft_foreach(tab, 0, f) ไม่เรียกเลย", g_buf, "");
	return (t_done());
}
