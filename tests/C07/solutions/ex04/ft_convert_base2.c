int	base_len(char *b)
{
	int	i;
	int	j;

	i = 0;
	while (b[i])
	{
		if (b[i] == '+' || b[i] == '-' || b[i] == ' '
			|| (b[i] >= 9 && b[i] <= 13))
			return (0);
		j = i + 1;
		while (b[j])
			if (b[i] == b[j++])
				return (0);
		i++;
	}
	if (i < 2)
		return (0);
	return (i);
}

int	base_idx(char c, char *b)
{
	int	i;

	i = 0;
	while (b[i])
	{
		if (b[i] == c)
			return (i);
		i++;
	}
	return (-1);
}
