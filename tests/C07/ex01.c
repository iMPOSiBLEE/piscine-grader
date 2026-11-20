#include "t.h"
int	*ft_range(int min, int max);
static void	c(int mn, int mx)
{
	char name[64]; int *t = ft_range(mn, mx);
	snprintf(name, 64, "ft_range(%d, %d)", mn, mx);
	if (mn >= mx) { t_ptr(name, t, NULL); return; }
	if (!t) { t_ko(name, "array", "NULL"); return; }
	for (int i = 0; i < mx - mn; i++) if (t[i] != mn + i) { char a[32], b[32]; snprintf(a, 32, "t[%d] = %d", i, mn + i); snprintf(b, 32, "t[%d] = %d", i, t[i]); t_ko(name, a, b); free(t); return; }
	t_ok(name); free(t);
}
int	main(void){ c(0, 5); c(-3, 3); c(5, 6); c(10, 10); c(10, 2); c(-2147483648, -2147483640); c(100, 1100); return (t_done()); }
