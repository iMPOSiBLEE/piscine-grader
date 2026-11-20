#include <stdlib.h>

int	base_len(char *b);
int	base_idx(char c, char *b);

long	to_long(char *s, char *b, int n)
{
	int		sign;
	long	v;

	sign = 1;
	v = 0;
	while (*s == ' ' || (*s >= 9 && *s <= 13))
		s++;
	while (*s == '+' || *s == '-')
	{
		if (*s == '-')
			sign = -sign;
		s++;
	}
	while (base_idx(*s, b) >= 0)
	{
		v = v * n + base_idx(*s, b);
		s++;
	}
	return (v * sign);
}

char	*fill(long v, char *base_to, int nt, int len)
{
	char	*res;
	long	t;

	res = malloc(len + 1);
	if (!res)
		return (NULL);
	res[len] = '\0';
	if (v < 0)
		res[0] = '-';
	if (v == 0)
		res[0] = base_to[0];
	t = v * (1 - 2 * (v < 0));
	while (t)
	{
		res[--len] = base_to[t % nt];
		t /= nt;
	}
	return (res);
}

char	*ft_convert_base(char *nbr, char *base_from, char *base_to)
{
	long	v;
	long	t;
	int		len;
	int		nt;

	nt = base_len(base_to);
	if (!base_len(base_from) || !nt)
		return (NULL);
	v = to_long(nbr, base_from, base_len(base_from));
	len = (v <= 0);
	t = v;
	while (t && ++len)
		t /= nt;
	return (fill(v, base_to, nt, len));
}
