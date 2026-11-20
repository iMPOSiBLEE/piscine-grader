#include <stdlib.h>
#include "ft_stock_str.h"

int	ft_len(char *s)
{
	int	i;

	i = 0;
	while (s[i])
		i++;
	return (i);
}

char	*ft_dup(char *s)
{
	char	*d;
	int		i;

	d = malloc(ft_len(s) + 1);
	if (!d)
		return (NULL);
	i = -1;
	while (s[++i])
		d[i] = s[i];
	d[i] = '\0';
	return (d);
}

struct s_stock_str	*ft_strs_to_tab(int ac, char **av)
{
	t_stock_str	*tab;
	int			i;

	tab = malloc(sizeof(t_stock_str) * (ac + 1));
	if (!tab)
		return (NULL);
	i = 0;
	while (i < ac)
	{
		tab[i].size = ft_len(av[i]);
		tab[i].str = av[i];
		tab[i].copy = ft_dup(av[i]);
		if (!tab[i].copy)
			return (NULL);
		i++;
	}
	tab[i].str = 0;
	tab[i].copy = 0;
	tab[i].size = 0;
	return (tab);
}
