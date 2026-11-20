#include "list.h"
void	ft_list_clear(t_list *begin_list, void (*free_fct)(void *));
static int g_n; static char g_seen[64];
static void	fr(void *d){ g_n++; strcat(g_seen, (char *)d); free(d); }
int	main(void)
{
	char *s[3]; s[0] = strdup("a"); s[1] = strdup("b"); s[2] = strdup("c");
	g_n = 0; g_seen[0] = 0; ft_list_clear(L(3, s), &fr);
	t_int("free_fct ถูกเรียกครบทุกตัว", g_n, 3); t_str("  เรียงตามลำดับ list", g_seen, "abc");
	g_n = 0; ft_list_clear(NULL, &fr); t_int("clear(NULL) ไม่เรียก free_fct", g_n, 0);
	return (t_done());
}
