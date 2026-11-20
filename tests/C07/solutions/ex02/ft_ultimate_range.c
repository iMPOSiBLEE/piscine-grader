#include <stdlib.h>

int	ft_ultimate_range(int **range, int min, int max)
{
	long	i;

	if (min >= max)
	{
		*range = NULL;
		return (0);
	}
	*range = malloc(sizeof(int) * ((long)max - min));
	if (!*range)
		return (-1);
	i = 0;
	while (min + i < max)
	{
		(*range)[i] = min + i;
		i++;
	}
	return (max - min);
}
