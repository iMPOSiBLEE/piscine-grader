#include "out.h"
void	ft_putchar(char c);
void	ft_swap(int *a, int *b);
void	ft_putstr(char *str);
int		ft_strlen(char *str);
int		ft_strcmp(char *s1, char *s2);
int	main(void)
{
	int a = 1, b = 2; char s[] = "Hello", x[] = "abc", y[] = "abd";
	T_OUT("ft_putchar('a') จาก libft.a", ft_putchar('a'), "a");
	T_OUT("ft_putstr(\"Hello\") จาก libft.a", ft_putstr(s), "Hello");
	ft_swap(&a, &b); t_int("ft_swap จาก libft.a", a * 10 + b, 21);
	t_int("ft_strlen(\"Hello\") จาก libft.a", ft_strlen(s), 5);
	t_cmp("ft_strcmp(\"abc\", \"abd\") จาก libft.a", ft_strcmp(x, y), -1);
	t_cmp("ft_strcmp(\"abc\", \"abc\") จาก libft.a", ft_strcmp(x, x), 0);
	return (t_done());
}
