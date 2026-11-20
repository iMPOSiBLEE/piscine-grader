#include "out.h"
void	ft_print_comb(void);
int	main(void)
{
	char	e[2000];
	int		n = 0;
	for (int a = 0; a <= 7; a++) for (int b = a + 1; b <= 8; b++) for (int c = b + 1; c <= 9; c++)
		n += sprintf(e + n, "%s%d%d%d", n ? ", " : "", a, b, c);
	T_OUT("ft_print_comb() (ต้องไม่มี , ต่อท้าย 789)", ft_print_comb(), e);
	return (t_done());
}
