#include "list.h"
t_list	*ft_list_last(t_list *begin_list);
int	main(void)
{
	char *s[] = {"a", "b", "c"}; t_list *l = L(3, s);
	t_ptr("ft_list_last([a,b,c]) ต้องได้ element c", ft_list_last(l), l->next->next);
	t_list *one = L(1, s); t_ptr("ft_list_last([a])", ft_list_last(one), one);
	t_ptr("ft_list_last(NULL) ต้องเป็น NULL", ft_list_last(NULL), NULL);
	return (t_done());
}
