#include <unistd.h>

void	ft_putstr(char *s)
{
	while (*s)
		write(1, s++, 1);
}

int	main(int argc, char **argv)
{
	while (--argc > 0)
	{
		ft_putstr(argv[argc]);
		write(1, "\n", 1);
	}
	return (0);
}
