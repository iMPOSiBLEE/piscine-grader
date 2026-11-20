#include "list.h"
void	ft_list_sort(t_list **begin_list, int (*cmp)());
static int	cmp(void *a, void *b){ return strcmp((char *)a, (char *)b); }
int	main(void)
{
	char *s[] = {"d", "b", "e", "a", "c", "b"}; char g[256]; t_list *l = L(6, s);
	ft_list_sort(&l, &cmp); dump(g, l); t_str("sort([d,b,e,a,c,b])", g, "[a,b,b,c,d,e]");
	t_list *o = L(1, s); ft_list_sort(&o, &cmp); dump(g, o); t_str("sort ตัวเดียว", g, "[d]");
	t_list *e = NULL; ft_list_sort(&e, &cmp); t_ptr("sort list ว่าง", e, NULL);
	return (t_done());
}
