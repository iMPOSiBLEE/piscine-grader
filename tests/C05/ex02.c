#include "t.h"
int	ft_iterative_power(int nb, int power);
static int	r(int n, int p){ int v = 1; if (p < 0) return 0; while (p-- > 0) v *= n; return v; }
int	main(void)
{
	int	v[][2] = {{2, 10}, {0, 0}, {5, 0}, {0, 3}, {2, -1}, {-2, 3}, {-3, 2}, {1, 100}, {10, 9}, {7, 1}};
	char	name[64];
	for (int i = 0; i < 10; i++) { snprintf(name, 64, "ft_iterative_power(%d, %d)", v[i][0], v[i][1]); t_int(name, ft_iterative_power(v[i][0], v[i][1]), r(v[i][0], v[i][1])); }
	return (t_done());
}
