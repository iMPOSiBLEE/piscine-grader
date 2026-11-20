#include <unistd.h>

void	print_addr(unsigned long addr)
{
	char	buf[16];
	char	*hex;
	int		i;

	hex = "0123456789abcdef";
	i = 15;
	while (i >= 0)
	{
		buf[i] = hex[addr % 16];
		addr = addr / 16;
		i--;
	}
	write(1, buf, 16);
	write(1, ": ", 2);
}

void	print_hex_part(unsigned char *p, unsigned int n)
{
	char			*hex;
	unsigned int	i;

	hex = "0123456789abcdef";
	i = 0;
	while (i < 16)
	{
		if (i < n)
		{
			write(1, &hex[p[i] / 16], 1);
			write(1, &hex[p[i] % 16], 1);
		}
		else
			write(1, "  ", 2);
		if (i % 2 == 1)
			write(1, " ", 1);
		i++;
	}
}

void	print_char_part(unsigned char *p, unsigned int n)
{
	unsigned int	i;

	i = 0;
	while (i < n)
	{
		if (p[i] >= 32 && p[i] <= 126)
			write(1, &p[i], 1);
		else
			write(1, ".", 1);
		i++;
	}
	write(1, "\n", 1);
}

void	*ft_print_memory(void *addr, unsigned int size)
{
	unsigned char	*p;
	unsigned int	pos;
	unsigned int	n;

	p = (unsigned char *)addr;
	pos = 0;
	while (pos < size)
	{
		n = size - pos;
		if (n > 16)
			n = 16;
		print_addr((unsigned long)(p + pos));
		print_hex_part(p + pos, n);
		print_char_part(p + pos, n);
		pos = pos + 16;
	}
	return (addr);
}
