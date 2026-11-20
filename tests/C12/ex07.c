#include "list.h"
t_list	*ft_list_at(t_list *begin_list, unsigned int nbr);
int	main(void)
{
	char *s[] = {"a", "b", "c"}; t_list *l = L(3, s);
	t_ptr("ft_list_at(l, 0) ตัวแรก", ft_list_at(l, 0), l);
	t_ptr("ft_list_at(l, 2) ตัวที่ 3", ft_list_at(l, 2), l->next->next);
	t_ptr("ft_list_at(l, 3) เกินขนาด ต้อง NULL", ft_list_at(l, 3), NULL);
	t_ptr("ft_list_at(l, 100) ต้อง NULL", ft_list_at(l, 100), NULL);
	t_ptr("ft_list_at(NULL, 0) ต้อง NULL", ft_list_at(NULL, 0), NULL);
	return (t_done());
}
