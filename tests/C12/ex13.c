#include "list.h"
void	ft_list_merge(t_list **begin_list1, t_list *begin_list2);
int	main(void)
{
	char *a[] = {"a", "b"}; char *b[] = {"c", "d"}; char g[256];
	t_list *l1 = L(2, a); t_list *l2 = L(2, b);
	ft_list_merge(&l1, l2); dump(g, l1); t_str("merge([a,b], [c,d])", g, "[a,b,c,d]");
	t_ptr("  ต้องใช้ element เดิมของ list2 (ห้ามสร้างใหม่)", l1->next->next, l2);
	t_list *e = NULL; t_list *l3 = L(2, b); ft_list_merge(&e, l3); t_ptr("merge(list ว่าง, list2) begin ต้องเป็น list2", e, l3);
	t_list *l4 = L(2, a); ft_list_merge(&l4, NULL); dump(g, l4); t_str("merge(list1, NULL)", g, "[a,b]");
	return (t_done());
}
