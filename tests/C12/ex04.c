#include "list.h"
void	ft_list_push_back(t_list **begin_list, void *data);
int	main(void)
{
	char *s[] = {"a", "b"}; char g[256]; t_list *l = L(2, s);
	ft_list_push_back(&l, "c"); dump(g, l); t_str("push_back(\"c\") ใส่ [a,b]", g, "[a,b,c]");
	t_list *e = NULL; ft_list_push_back(&e, "x"); dump(g, e); t_str("push_back ใส่ list ว่าง (ต้องอัปเดต begin)", g, "[x]");
	ft_list_push_back(&e, "y"); dump(g, e); t_str("push_back อีกตัว", g, "[x,y]");
	return (t_done());
}
