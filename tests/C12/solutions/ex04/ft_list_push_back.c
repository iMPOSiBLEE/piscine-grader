#include "ft_list.h"

void	ft_list_push_back(t_list **begin_list, void *data)
{
	t_list	*cur;

	if (!*begin_list)
	{
		*begin_list = ft_create_elem(data);
		return ;
	}
	cur = *begin_list;
	while (cur->next)
		cur = cur->next;
	cur->next = ft_create_elem(data);
}
