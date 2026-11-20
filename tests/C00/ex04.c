#include "out.h"
#include <limits.h>
void	ft_is_negative(int n);
int	main(void)
{
	T_OUT("ft_is_negative(-5)", ft_is_negative(-5), "N");
	T_OUT("ft_is_negative(0)", ft_is_negative(0), "P");
	T_OUT("ft_is_negative(42)", ft_is_negative(42), "P");
	T_OUT("ft_is_negative(INT_MIN)", ft_is_negative(INT_MIN), "N");
	T_OUT("ft_is_negative(INT_MAX)", ft_is_negative(INT_MAX), "P");
	return (t_done());
}
