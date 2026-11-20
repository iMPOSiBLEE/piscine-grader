#include "list.h"
int	ft_list_size(t_list *begin_list);
int	main(void)
{
	char *s[] = {"a", "b", "c", "d"};
	t_int("ft_list_size([a,b,c,d])", ft_list_size(L(4, s)), 4);
	t_int("ft_list_size([a])", ft_list_size(L(1, s)), 1);
	t_int("ft_list_size(NULL)", ft_list_size(NULL), 0);
	return (t_done());
}
