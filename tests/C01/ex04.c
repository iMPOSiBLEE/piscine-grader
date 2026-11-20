#include "t.h"
void	ft_ultimate_div_mod(int *a, int *b);
int	main(void)
{
	int v[][2] = {{42, 5}, {10, 2}, {-7, 2}, {7, -2}, {0, 3}, {3, 7}};
	char name[64]; int a, b;
	for (int i = 0; i < 6; i++) { a = v[i][0]; b = v[i][1]; ft_ultimate_div_mod(&a, &b);
		snprintf(name, 64, "ultimate_div_mod(%d, %d) → *a", v[i][0], v[i][1]); t_int(name, a, v[i][0] / v[i][1]);
		snprintf(name, 64, "ultimate_div_mod(%d, %d) → *b", v[i][0], v[i][1]); t_int(name, b, v[i][0] % v[i][1]); }
	return (t_done());
}
