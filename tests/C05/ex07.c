#include "t.h"
int	ft_find_next_prime(int nb);
static int	p(int n){ if (n < 2) return 0; for (long i = 2; i * i <= n; i++) if (n % i == 0) return 0; return 1; }
static int	r(int n){ if (n < 2) return 2; while (!p(n)) n++; return n; }
int	main(void)
{
	int	v[] = {-10, 0, 1, 2, 3, 4, 14, 17, 24, 100, 2147483646, 2147483647};
	char	name[64];
	for (int i = 0; i < 12; i++) { snprintf(name, 64, "ft_find_next_prime(%d)", v[i]); t_int(name, ft_find_next_prime(v[i]), r(v[i])); }
	return (t_done());
}
