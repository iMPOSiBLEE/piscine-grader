#include <fcntl.h>
#include <unistd.h>

void	ft_puterr(char *s)
{
	while (*s)
		write(2, s++, 1);
}

int	main(int argc, char **argv)
{
	char	buf[4096];
	int		fd;
	int		n;

	if (argc < 2)
		ft_puterr("File name missing.\n");
	if (argc > 2)
		ft_puterr("Too many arguments.\n");
	if (argc != 2)
		return (1);
	fd = open(argv[1], O_RDONLY);
	if (fd < 0)
	{
		ft_puterr("Cannot read file.\n");
		return (1);
	}
	n = read(fd, buf, 4096);
	while (n > 0)
	{
		write(1, buf, n);
		n = read(fd, buf, 4096);
	}
	close(fd);
	return (0);
}
