#include "list.h"
void	ft_sorted_list_insert(t_list **begin_list, void *data, int (*cmp)());
static int	cmp(void *a, void *b){ return strcmp((char *)a, (char *)b); }
int	main(void)
{
	char *s[] = {"b", "d", "f"}; char g[256]; t_list *l;
	l = L(3, s); ft_sorted_list_insert(&l, "c", &cmp); dump(g, l); t_str("insert(\"c\") ตรงกลาง", g, "[b,c,d,f]");
	l = L(3, s); ft_sorted_list_insert(&l, "a", &cmp); dump(g, l); t_str("insert(\"a\") หัว list", g, "[a,b,d,f]");
	l = L(3, s); ft_sorted_list_insert(&l, "z", &cmp); dump(g, l); t_str("insert(\"z\") ท้าย list", g, "[b,d,f,z]");
	l = NULL; ft_sorted_list_insert(&l, "x", &cmp); dump(g, l); t_str("insert ใน list ว่าง", g, "[x]");
	return (t_done());
}
