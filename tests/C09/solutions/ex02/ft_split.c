#include <stdlib.h>

int	is_sep(char c, char *cs)
{
	while (*cs)
		if (*cs++ == c)
			return (1);
	return (0);
}

int	count_words(char *s, char *cs)
{
	int	n;

	n = 0;
	while (*s)
	{
		while (*s && is_sep(*s, cs))
			s++;
		if (*s)
			n++;
		while (*s && !is_sep(*s, cs))
			s++;
	}
	return (n);
}

char	*dup_word(char *s, int len)
{
	char	*w;
	int		i;

	w = malloc(len + 1);
	if (!w)
		return (NULL);
	i = -1;
	while (++i < len)
		w[i] = s[i];
	w[len] = '\0';
	return (w);
}

char	**ft_split(char *str, char *charset)
{
	char	**tab;
	int		i;
	int		len;

	tab = malloc(sizeof(char *) * (count_words(str, charset) + 1));
	if (!tab)
		return (NULL);
	i = 0;
	while (*str)
	{
		while (*str && is_sep(*str, charset))
			str++;
		len = 0;
		while (str[len] && !is_sep(str[len], charset))
			len++;
		if (len)
			tab[i++] = dup_word(str, len);
		str += len;
	}
	tab[i] = 0;
	return (tab);
}
