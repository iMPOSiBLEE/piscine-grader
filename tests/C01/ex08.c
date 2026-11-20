#include "t.h"
#include <limits.h>
void	ft_sort_int_tab(int *tab, int size);
static void	arr(char *b, int *t, int n){ int k = sprintf(b, "["); for (int i = 0; i < n; i++) k += sprintf(b + k, "%s%d", i ? ", " : "", t[i]); sprintf(b + k, "]"); }
static int	cmp(const void *a, const void *b){ int x = *(int *)a, y = *(int *)b; return (x > y) - (x < y); }
static void	c(const char *name, int *t, int n)
{
	int e[20]; char g[512], w[512];
	memcpy(e, t, n * sizeof(int)); qsort(e, n, sizeof(int), cmp);
	ft_sort_int_tab(t, n); arr(g, t, n); arr(w, e, n); t_str(name, g, w);
}
int	main(void)
{
	int a[] = {5, 3, 1, 4, 2}; int b[] = {1, 2, 3}; int d[] = {3, 3, 1, 1, 2}; int e[] = {42};
	int f[] = {INT_MAX, -1, INT_MIN, 0, 7}; int g[] = {9, 8, 7, 6, 5, 4, 3, 2, 1, 0};
	c("เรียง [5,3,1,4,2]", a, 5); c("เรียงอยู่แล้ว", b, 3); c("มีเลขซ้ำ", d, 5); c("ตัวเดียว", e, 1);
	c("มีติดลบ + INT_MIN/INT_MAX", f, 5); c("เรียงกลับด้าน 10 ตัว", g, 10);
	return (t_done());
}
