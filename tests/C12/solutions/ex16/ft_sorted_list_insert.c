#include "ft_list.h"

void	ft_sorted_list_insert(t_list **begin_list, void *data, int (*cmp)())
{
	t_list	*elem;
	t_list	*cur;

	elem = ft_create_elem(data);
	if (!elem)
		return ;
	if (!*begin_list || (*cmp)(data, (*begin_list)->data) < 0)
	{
		elem->next = *begin_list;
		*begin_list = elem;
		return ;
	}
	cur = *begin_list;
	while (cur->next && (*cmp)(cur->next->data, data) <= 0)
		cur = cur->next;
	elem->next = cur->next;
	cur->next = elem;
}
