#include "list.h"
void	ft_list_foreach_if(t_list *begin_list, void (*f)(void *), void *data_ref, int (*cmp)());
static char g_s[64];
static void	f(void *d){ strcat(g_s, (char *)d); strcat(g_s, ","); }
static int	cmp(void *a, void *b){ return strcmp((char *)a, (char *)b); }
int	main(void)
{
	char *s[] = {"x", "y", "x", "z", "x"};
	g_s[0] = 0; ft_list_foreach_if(L(5, s), &f, "x", &cmp); t_str("foreach_if เฉพาะตัวที่ cmp == 0", g_s, "x,x,x,");
	g_s[0] = 0; ft_list_foreach_if(L(5, s), &f, "q", &cmp); t_str("ไม่มีตัวที่ตรง", g_s, "");
	return (t_done());
}
