#include <fcntl.h>
#include <unistd.h>
#include <string.h>
#include <errno.h>
#include <libgen.h>

void	ft_puterr(char *s)
{
	while (*s)
		write(2, s++, 1);
}

void	print_error(char *prog, char *file)
{
	ft_puterr(basename(prog));
	ft_puterr(": ");
	ft_puterr(file);
	ft_puterr(": ");
	ft_puterr(strerror(errno));
	ft_puterr("\n");
}

int	dump_fd(int fd, char *prog, char *name)
{
	char	buf[29000];
	int		n;

	n = read(fd, buf, 29000);
	while (n > 0)
	{
		write(1, buf, n);
		n = read(fd, buf, 29000);
	}
	if (n < 0)
	{
		print_error(prog, name);
		return (1);
	}
	return (0);
}

int	cat_file(char *prog, char *name)
{
	int	fd;
	int	ret;

	if (name[0] == '-' && name[1] == '\0')
		return (dump_fd(0, prog, name));
	fd = open(name, O_RDONLY);
	if (fd < 0)
	{
		print_error(prog, name);
		return (1);
	}
	ret = dump_fd(fd, prog, name);
	close(fd);
	return (ret);
}

int	main(int argc, char **argv)
{
	int	i;
	int	ret;

	if (argc == 1)
		return (dump_fd(0, argv[0], "-"));
	ret = 0;
	i = 1;
	while (i < argc)
	{
		if (cat_file(argv[0], argv[i]))
			ret = 1;
		i++;
	}
	return (ret);
}
