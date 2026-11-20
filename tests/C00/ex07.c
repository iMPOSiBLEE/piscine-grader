#include "out.h"
#include <limits.h>
void	ft_putnbr(int nb);
#define P(v, s) T_OUT("ft_putnbr(" #v ")", ft_putnbr(v), s)
int	main(void)
{
	P(0, "0"); P(7, "7"); P(42, "42"); P(-42, "-42"); P(100, "100"); P(-9, "-9");
	P(INT_MAX, "2147483647"); P(INT_MIN, "-2147483648"); P(-1000000, "-1000000");
	return (t_done());
}
