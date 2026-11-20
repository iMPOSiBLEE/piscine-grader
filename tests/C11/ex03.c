#include "t.h"
int	ft_count_if(char **tab, int length, int (*f)(char *));
static int	has_a(char *s){ return strchr(s, 'a') != NULL; }
int	main(void)
{
	char *a[] = {"banana", "kiwi", "apple", "plum", "pear"};
	t_int("ft_count_if(5 ผลไม้, มีตัว a)", ft_count_if(a, 5, &has_a), 3);
	t_int("ft_count_if(2 ตัวแรก, มีตัว a)", ft_count_if(a, 2, &has_a), 1);
	t_int("ft_count_if(length 0)", ft_count_if(a, 0, &has_a), 0);
	return (t_done());
}
