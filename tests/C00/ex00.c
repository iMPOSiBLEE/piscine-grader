#include "out.h"
void	ft_putchar(char c);
int	main(void)
{
	T_OUT("ft_putchar('a')", ft_putchar('a'), "a");
	T_OUT("ft_putchar('Z')", ft_putchar('Z'), "Z");
	T_OUT("ft_putchar('0')", ft_putchar('0'), "0");
	T_OUT("ft_putchar('\\n')", ft_putchar('\n'), "\n");
	T_OUT("ft_putchar(' ')", ft_putchar(' '), " ");
	return (t_done());
}
