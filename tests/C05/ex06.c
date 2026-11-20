#include "t.h"
int	ft_is_prime(int nb);
static int	r(int n){ if (n < 2) return 0; for (long i = 2; i * i <= n; i++) if (n % i == 0) return 0; return 1; }
int	main(void)
{
	int	v[] = {-7, 0, 1, 2, 3, 4, 17, 25, 97, 100, 7919, 2147483647, 2147483646};
	char	name[64];
	for (int i = 0; i < 13; i++) { snprintf(name, 64, "ft_is_prime(%d)", v[i]); t_int(name, ft_is_prime(v[i]), r(v[i])); }
	return (t_done());
}
