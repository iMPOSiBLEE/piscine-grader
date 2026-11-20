#include "t.h"
int	ft_fibonacci(int index);
static int	r(int n){ int a = 0, b = 1, t; if (n < 0) return -1; while (n-- > 0) { t = a + b; a = b; b = t; } return a; }
int	main(void)
{
	int	v[] = {-10, -1, 0, 1, 2, 3, 10, 20, 30};
	char	name[64];
	for (int i = 0; i < 9; i++) { snprintf(name, 64, "ft_fibonacci(%d)", v[i]); t_int(name, ft_fibonacci(v[i]), r(v[i])); }
	return (t_done());
}
