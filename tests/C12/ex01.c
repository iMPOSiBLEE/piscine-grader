#include "list.h"
void	ft_list_push_front(t_list **begin_list, void *data);
int	main(void)
{
	char *s[] = {"b", "c"}; char g[256]; t_list *l = L(2, s);
	ft_list_push_front(&l, "a"); dump(g, l); t_str("push_front(\"a\") ใส่ [b,c]", g, "[a,b,c]");
	t_list *e = NULL; ft_list_push_front(&e, "x"); dump(g, e); t_str("push_front ใส่ list ว่าง", g, "[x]");
	return (t_done());
}
