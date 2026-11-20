#include "t.h"
void	ft_sort_string_tab(char **tab);
static void	join(char *o, char **t){ int k = 0; for (int i = 0; t[i]; i++) k += sprintf(o + k, "%s,", t[i]); o[k] = 0; }
int	main(void)
{
	char *a[] = {"pear", "Apple", "banana", "apple", "42", "", "b", 0}; char g[256];
	char *orig = a[2];
	ft_sort_string_tab(a); join(g, a);
	t_str("เรียงตาม ASCII", g, ",42,Apple,apple,b,banana,pear,");
	int found = 0; for (int i = 0; a[i]; i++) if (a[i] == orig) found = 1;
	t_int("  ต้องสลับ pointer (ไม่ก๊อป string)", found, 1);
	char *b[] = {0}; ft_sort_string_tab(b); t_ok("array ว่างไม่พัง");
	char *c[] = {"z", 0}; ft_sort_string_tab(c); join(g, c); t_str("ตัวเดียว", g, "z,");
	return (t_done());
}
