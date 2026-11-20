#include "t.h"
int	*ft_map(int *tab, int length, int (*f)(int));
static int	dbl(int x){ return x * 2; }
static int	neg(int x){ return -x; }
int	main(void)
{
	int t[] = {1, 2, 3, -4, 0};
	int *r = ft_map(t, 5, &dbl);
	char g[128], e[] = "2,4,6,-8,0,"; int k = 0;
	if (!r) { t_ko("ft_map(tab, 5, x*2)", e, "NULL"); return (t_done()); }
	for (int i = 0; i < 5; i++) k += sprintf(g + k, "%d,", r[i]);
	t_str("ft_map(tab, 5, x*2)", g, e);
	if (r == t) t_ko("  ต้องคืน array ใหม่ (malloc)", "pointer ใหม่", "pointer เดิม"); else t_ok("  คืน array ใหม่");
	t_int("  tab เดิมต้องไม่ถูกแก้", t[0], 1);
	free(r);
	r = ft_map(t, 3, &neg); k = 0;
	for (int i = 0; r && i < 3; i++) k += sprintf(g + k, "%d,", r[i]);
	t_str("ft_map(tab, 3, -x)", r ? g : "NULL", "-1,-2,-3,");
	free(r);
	return (t_done());
}
