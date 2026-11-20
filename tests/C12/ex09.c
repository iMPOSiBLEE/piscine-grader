#include "list.h"
void	ft_list_foreach(t_list *begin_list, void (*f)(void *));
static char g_s[64];
static void	f(void *d){ strcat(g_s, (char *)d); }
int	main(void)
{
	char *s[] = {"a", "b", "c"};
	g_s[0] = 0; ft_list_foreach(L(3, s), &f); t_str("foreach เรียก f ตามลำดับ", g_s, "abc");
	g_s[0] = 0; ft_list_foreach(NULL, &f); t_str("foreach(NULL)", g_s, "");
	return (t_done());
}
