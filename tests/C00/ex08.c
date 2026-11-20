#include "out.h"
void	ft_print_combn(int n);
static char	g_e[4000000];
static int	g_len;
static int	g_d[10];
static void	gen(int n, int pos, int start)
{
	if (pos == n) { if (g_len) { g_e[g_len++] = ','; g_e[g_len++] = ' '; }
		for (int i = 0; i < n; i++) g_e[g_len++] = '0' + g_d[i]; return; }
	for (int v = start; v <= 9; v++) { g_d[pos] = v; gen(n, pos + 1, v + 1); }
}
int	main(void)
{
	char	name[64];
	for (int n = 1; n <= 9; n++)
	{
		g_len = 0; gen(n, 0, 0); g_e[g_len] = 0;
		snprintf(name, 64, "ft_print_combn(%d)", n);
		T_OUT(name, ft_print_combn(n), g_e);
	}
	return (t_done());
}
