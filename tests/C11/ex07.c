#include "t.h"
void	ft_advanced_sort_string_tab(char **tab, int (*cmp)(char *, char *));
static void	join(char *o, char **t){ int k = 0; for (int i = 0; t[i]; i++) k += sprintf(o + k, "%s,", t[i]); o[k] = 0; }
static int	by_len(char *a, char *b){ return (int)strlen(a) - (int)strlen(b); }
static int	rev(char *a, char *b){ return strcmp(b, a); }
static int	cmp(char *a, char *b){ return strcmp(a, b); }
int	main(void)
{
	char g[256];
	char *a[] = {"pear", "Apple", "banana", "42", "b", 0}; ft_advanced_sort_string_tab(a, &cmp); join(g, a);
	t_str("cmp = strcmp", g, "42,Apple,b,banana,pear,");
	char *b[] = {"pear", "Apple", "banana", "42", "b", 0}; ft_advanced_sort_string_tab(b, &rev); join(g, b);
	t_str("cmp = เรียงกลับด้าน", g, "pear,banana,b,Apple,42,");
	char *c[] = {"ccc", "a", "bb", "dddd", 0}; ft_advanced_sort_string_tab(c, &by_len); join(g, c);
	t_str("cmp = ตามความยาว", g, "a,bb,ccc,dddd,");
	return (t_done());
}
