#include <unistd.h>

void	print_digits(int *d, int n, int *first)
{
	int		i;
	char	c;

	if (!*first)
		write(1, ", ", 2);
	*first = 0;
	i = 0;
	while (i < n)
	{
		c = d[i] + '0';
		write(1, &c, 1);
		i++;
	}
}

void	gen(int *d, int n, int pos, int *first)
{
	int	v;

	if (pos == n)
	{
		print_digits(d, n, first);
		return ;
	}
	if (pos == 0)
		v = 0;
	else
		v = d[pos - 1] + 1;
	while (v <= 9)
	{
		d[pos] = v;
		gen(d, n, pos + 1, first);
		v++;
	}
}

void	ft_print_combn(int n)
{
	int	d[10];
	int	first;

	if (n <= 0 || n >= 10)
		return ;
	first = 1;
	gen(d, n, 0, &first);
}
