#include "list.h"
void	ft_list_reverse_fun(t_list *begin_list);
int	main(void)
{
	char *s[] = {"a", "b", "c", "d", "e"}; char g[256]; t_list *l = L(5, s);
	ft_list_reverse_fun(l); dump(g, l); t_str("reverse_fun([a,b,c,d,e]) (begin เดิม)", g, "[e,d,c,b,a]");
	t_list *l2 = L(4, s); ft_list_reverse_fun(l2); dump(g, l2); t_str("reverse_fun([a,b,c,d])", g, "[d,c,b,a]");
	t_list *o = L(1, s); ft_list_reverse_fun(o); dump(g, o); t_str("ตัวเดียว", g, "[a]");
	ft_list_reverse_fun(NULL); t_ok("NULL ไม่พัง");
	return (t_done());
}
