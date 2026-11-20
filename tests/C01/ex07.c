#include "t.h"
void	ft_rev_int_tab(int *tab, int size);
static void	arr(char *b, int *t, int n){ int k = sprintf(b, "["); for (int i = 0; i < n; i++) k += sprintf(b + k, "%s%d", i ? ", " : "", t[i]); sprintf(b + k, "]"); }
static void	c(const char *name, int *t, int n)
{
	int e[20]; char g[256], w[256];
	for (int i = 0; i < n; i++) e[i] = t[n - 1 - i];
	ft_rev_int_tab(t, n); arr(g, t, n); arr(w, e, n); t_str(name, g, w);
}
int	main(void)
{
	int a[] = {1, 2, 3, 4, 5}; int b[] = {1, 2, 3, 4, 5, 6}; int d[] = {42}; int e[] = {-1, 7};
	c("กลับ [1,2,3,4,5]", a, 5); c("กลับ [1..6] (จำนวนคู่)", b, 6); c("กลับ [42] (ตัวเดียว)", d, 1); c("กลับ [-1,7]", e, 2);
	return (t_done());
}
