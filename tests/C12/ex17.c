#include "list.h"
void	ft_sorted_list_merge(t_list **begin_list1, t_list *begin_list2, int (*cmp)());
static int	cmp(void *a, void *b){ return strcmp((char *)a, (char *)b); }
int	main(void)
{
	char *a[] = {"a", "d", "f"}; char *b[] = {"b", "c", "e", "g"}; char g[256]; t_list *l;
	l = L(3, a); ft_sorted_list_merge(&l, L(4, b), &cmp); dump(g, l); t_str("merge([a,d,f], [b,c,e,g])", g, "[a,b,c,d,e,f,g]");
	l = NULL; ft_sorted_list_merge(&l, L(4, b), &cmp); dump(g, l); t_str("merge(ว่าง, [b,c,e,g])", g, "[b,c,e,g]");
	l = L(3, a); ft_sorted_list_merge(&l, NULL, &cmp); dump(g, l); t_str("merge([a,d,f], ว่าง)", g, "[a,d,f]");
	return (t_done());
}
