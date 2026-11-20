#include <unistd.h>

void	ft_putstr_fd(char *s, int fd)
{
	while (*s)
		write(fd, s++, 1);
}

void	put_hex(unsigned long n, int width)
{
	char	buf[16];
	int		i;

	i = width;
	while (i-- > 0)
	{
		buf[i] = "0123456789abcdef"[n % 16];
		n /= 16;
	}
	write(1, buf, width);
}

void	print_line(unsigned char *b, int len, unsigned long off)
{
	int	i;

	put_hex(off, 8);
	write(1, "  ", 2);
	i = -1;
	while (++i < 16)
	{
		if (i < len)
			put_hex(b[i], 2);
		else
			write(1, "  ", 2);
		write(1, " ", 1);
		if (i == 7)
			write(1, " ", 1);
	}
	write(1, " |", 2);
	i = -1;
	while (++i < len)
	{
		if (b[i] >= 32 && b[i] < 127)
			write(1, &b[i], 1);
		else
			write(1, ".", 1);
	}
	write(1, "|\n", 2);
}

int	same(unsigned char *a, unsigned char *b)
{
	int	i;

	i = 0;
	while (i < 16 && a[i] == b[i])
		i++;
	return (i == 16);
}
