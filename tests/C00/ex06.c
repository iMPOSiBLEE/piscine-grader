#include "out.h"
void	ft_print_comb2(void);
int	main(void)
{
	static char	e[40000];
	int		n = 0;
	for (int a = 0; a <= 98; a++) for (int b = a + 1; b <= 99; b++)
		n += sprintf(e + n, "%s%02d %02d", n ? ", " : "", a, b);
	T_OUT("ft_print_comb2() (00 01, ..., 98 99)", ft_print_comb2(), e);
	return (t_done());
}
