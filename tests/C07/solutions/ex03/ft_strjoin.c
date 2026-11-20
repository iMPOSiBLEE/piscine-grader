#include <stdlib.h>

int	ft_len(char *s)
{
	int	i;

	i = 0;
	while (s[i])
		i++;
	return (i);
}

char	*ft_cat(char *dst, char *src)
{
	while (*src)
		*dst++ = *src++;
	return (dst);
}

char	*ft_strjoin(int size, char **strs, char *sep)
{
	char	*res;
	char	*p;
	int		total;
	int		i;

	total = 1;
	i = -1;
	while (++i < size)
		total += ft_len(strs[i]) + ft_len(sep);
	res = malloc(total);
	if (!res)
		return (NULL);
	p = res;
	i = -1;
	while (++i < size)
	{
		if (i > 0)
			p = ft_cat(p, sep);
		p = ft_cat(p, strs[i]);
	}
	*p = '\0';
	return (res);
}
