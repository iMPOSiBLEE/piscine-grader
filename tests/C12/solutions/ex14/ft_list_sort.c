#include "ft_list.h"

void	ft_list_sort(t_list **begin_list, int (*cmp)())
{
	t_list	*a;
	t_list	*b;
	void	*tmp;

	a = *begin_list;
	while (a)
	{
		b = a->next;
		while (b)
		{
			if ((*cmp)(a->data, b->data) > 0)
			{
				tmp = a->data;
				a->data = b->data;
				b->data = tmp;
			}
			b = b->next;
		}
		a = a->next;
	}
}
