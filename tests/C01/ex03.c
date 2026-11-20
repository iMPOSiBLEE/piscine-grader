#include "t.h"
void	ft_div_mod(int a, int b, int *div, int *mod);
int	main(void)
{
	int v[][2] = {{42, 5}, {10, 2}, {-7, 2}, {7, -2}, {0, 3}, {3, 7}};
	char name[64]; int d, m;
	for (int i = 0; i < 6; i++) { d = m = 12345; ft_div_mod(v[i][0], v[i][1], &d, &m);
		snprintf(name, 64, "ft_div_mod(%d, %d) div", v[i][0], v[i][1]); t_int(name, d, v[i][0] / v[i][1]);
		snprintf(name, 64, "ft_div_mod(%d, %d) mod", v[i][0], v[i][1]); t_int(name, m, v[i][0] % v[i][1]); }
	return (t_done());
}
