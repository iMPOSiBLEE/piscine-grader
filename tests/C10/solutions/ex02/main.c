#include <fcntl.h>
#include <unistd.h>
#include <stdlib.h>

void	ft_putstr_fd(char *s, int fd);
void	print_error(char *prog, char *file);
int		ft_atoi(char *s);

char	*join_buf(char *buf, int size, char *tmp, int n)
{
	char	*out;
	int		i;

	out = malloc(size + n);
	if (!out)
		return (NULL);
	i = -1;
	while (++i < size)
		out[i] = buf[i];
	i = -1;
	while (++i < n)
		out[size + i] = tmp[i];
	free(buf);
	return (out);
}

int	read_all(int fd, char **out)
{
	char	tmp[4096];
	int		size;
	int		n;

	size = 0;
	*out = malloc(1);
	n = read(fd, tmp, 4096);
	while (n > 0 && *out)
	{
		*out = join_buf(*out, size, tmp, n);
		size += n;
		n = read(fd, tmp, 4096);
	}
	return (size);
}

int	tail_file(char *prog, char *name, int count)
{
	int		fd;
	int		size;
	char	*data;

	fd = open(name, O_RDONLY);
	if (fd < 0)
	{
		print_error(prog, name);
		return (1);
	}
	size = read_all(fd, &data);
	close(fd);
	if (count > size)
		count = size;
	write(1, data + size - count, count);
	free(data);
	return (0);
}

void	print_header(char *name, int *first)
{
	if (!*first)
		ft_putstr_fd("\n", 1);
	ft_putstr_fd("==> ", 1);
	ft_putstr_fd(name, 1);
	ft_putstr_fd(" <==\n", 1);
	*first = 0;
}

int	main(int argc, char **argv)
{
	int	i;
	int	ret;
	int	count;
	int	first;
	int	fd;

	if (argc < 4)
		return (1);
	count = ft_atoi(argv[2]);
	ret = 0;
	first = 1;
	i = 2;
	while (++i < argc)
	{
		fd = open(argv[i], O_RDONLY);
		if (fd >= 0 && argc > 4)
			print_header(argv[i], &first);
		if (fd >= 0)
			close(fd);
		if (tail_file(argv[0], argv[i], count))
			ret = 1;
	}
	return (ret);
}
