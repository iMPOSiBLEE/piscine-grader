#include "list.h"
void	ft_list_reverse(t_list **begin_list);
int	main(void)
{
	char *s[] = {"a", "b", "c", "d"}; char g[256]; t_list *l = L(4, s);
	ft_list_reverse(&l); dump(g, l); t_str("reverse([a,b,c,d])", g, "[d,c,b,a]");
	t_list *o = L(1, s); ft_list_reverse(&o); dump(g, o); t_str("reverse([a])", g, "[a]");
	t_list *e = NULL; ft_list_reverse(&e); t_ptr("reverse(list ว่าง)", e, NULL);
	return (t_done());
}
