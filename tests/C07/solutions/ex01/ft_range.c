#include <stdlib.h>

int	*ft_range(int min, int max)
{
	int		*tab;
	long	i;

	if (min >= max)
		return (NULL);
	tab = malloc(sizeof(int) * ((long)max - min));
	if (!tab)
		return (NULL);
	i = 0;
	while (min + i < max)
	{
		tab[i] = min + i;
		i++;
	}
	return (tab);
}
