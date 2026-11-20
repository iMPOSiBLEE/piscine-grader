#include <unistd.h>
#include "do_op.h"

int	ft_atoi(char *s)
{
	int		sign;
	long	v;

	sign = 1;
	v = 0;
	while (*s == ' ' || (*s >= 9 && *s <= 13))
		s++;
	while (*s == '+' || *s == '-')
	{
		if (*s == '-')
			sign = -sign;
		s++;
	}
	while (*s >= '0' && *s <= '9')
		v = v * 10 + (*s++ - '0');
	return ((int)(v * sign));
}

void	ft_putnbr(int nb)
{
	long	n;
	char	c;

	n = nb;
	if (n < 0)
	{
		write(1, "-", 1);
		n = -n;
	}
	if (n >= 10)
		ft_putnbr(n / 10);
	c = n % 10 + '0';
	write(1, &c, 1);
}

int	op_index(char *op)
{
	char	*ops;
	int		i;

	ops = "+-/*%";
	if (!op[0] || op[1])
		return (-1);
	i = 0;
	while (ops[i])
	{
		if (ops[i] == op[0])
			return (i);
		i++;
	}
	return (-1);
}

int	main(int argc, char **argv)
{
	int		(*f[5])(int, int);
	int		i;
	int		b;

	if (argc != 4)
		return (0);
	f[0] = op_add;
	f[1] = op_sub;
	f[2] = op_div;
	f[3] = op_mul;
	f[4] = op_mod;
	i = op_index(argv[2]);
	b = ft_atoi(argv[3]);
	if (i == 2 && b == 0)
		write(1, "Stop : division by zero", 23);
	else if (i == 4 && b == 0)
		write(1, "Stop : modulo by zero", 21);
	else if (i < 0)
		write(1, "0", 1);
	else
		ft_putnbr(f[i](ft_atoi(argv[1]), b));
	write(1, "\n", 1);
	return (0);
}
