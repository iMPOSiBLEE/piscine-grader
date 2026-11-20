#include <fcntl.h>
#include <unistd.h>
#include <string.h>
#include <errno.h>
#include <libgen.h>
#include "hexdump.h"

void	ft_putstr_fd(char *s, int fd);
void	put_hex(unsigned long n, int width);
void	print_line(unsigned char *b, int len, unsigned long off);
int		same(unsigned char *a, unsigned char *b);

void	flush_line(t_hd *h)
{
	int	i;

	if (h->has_prev && h->len == 16 && same(h->line, h->prev))
	{
		if (!h->star)
			ft_putstr_fd("*\n", 1);
		h->star = 1;
	}
	else
	{
		print_line(h->line, h->len, h->off);
		h->star = 0;
	}
	i = -1;
	while (++i < 16)
		h->prev[i] = h->line[i];
	h->has_prev = 1;
	h->off += h->len;
	h->len = 0;
}

void	feed(t_hd *h, int fd)
{
	unsigned char	buf[4096];
	int				n;
	int				i;

	n = read(fd, buf, 4096);
	while (n > 0)
	{
		i = 0;
		while (i < n)
		{
			h->line[h->len++] = buf[i++];
			if (h->len == 16)
				flush_line(h);
		}
		n = read(fd, buf, 4096);
	}
}

int	open_feed(t_hd *h, char *prog, char *name)
{
	int	fd;

	fd = open(name, O_RDONLY);
	if (fd < 0)
	{
		ft_putstr_fd(basename(prog), 2);
		ft_putstr_fd(": ", 2);
		ft_putstr_fd(name, 2);
		ft_putstr_fd(": ", 2);
		ft_putstr_fd(strerror(errno), 2);
		ft_putstr_fd("\n", 2);
		return (1);
	}
	feed(h, fd);
	close(fd);
	return (0);
}

int	main(int argc, char **argv)
{
	t_hd	h;
	int		i;
	int		ret;

	h.len = 0;
	h.has_prev = 0;
	h.star = 0;
	h.off = 0;
	ret = 0;
	i = 1;
	while (++i < argc)
		ret |= open_feed(&h, argv[0], argv[i]);
	if (argc < 3)
		feed(&h, 0);
	if (h.len > 0)
		flush_line(&h);
	if (h.off > 0)
	{
		put_hex(h.off, 8);
		write(1, "\n", 1);
	}
	return (ret);
}
