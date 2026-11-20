#include "t.h"
int	ft_recursive_factorial(int nb);
static int	r(int n){ int v = 1; if (n < 0) return 0; while (n > 1) v *= n--; return v; }
int	main(void)
{
	int	v[] = {-5, -1, 0, 1, 2, 3, 5, 10, 12};
	char	name[64];
	for (int i = 0; i < 9; i++) { snprintf(name, 64, "ft_recursive_factorial(%d)", v[i]); t_int(name, ft_recursive_factorial(v[i]), r(v[i])); }
	return (t_done());
}
