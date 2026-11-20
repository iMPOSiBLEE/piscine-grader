#include "t.h"
int	ft_sqrt(int nb);
static int	r(int n){ long i = 1; if (n <= 0) return 0; while (i * i < n) i++; return (i * i == n) ? (int)i : 0; }
int	main(void)
{
	int	v[] = {-4, 0, 1, 2, 4, 9, 10, 16, 25, 26, 144, 2147395600, 2147483647};
	char	name[64];
	for (int i = 0; i < 13; i++) { snprintf(name, 64, "ft_sqrt(%d)", v[i]); t_int(name, ft_sqrt(v[i]), r(v[i])); }
	return (t_done());
}
