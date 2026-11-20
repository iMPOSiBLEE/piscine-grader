#include "ft_list.h"

int	list_len(t_list *l)
{
	int	n;

	n = 0;
	while (l)
	{
		n++;
		l = l->next;
	}
	return (n);
}

t_list	*list_at(t_list *l, int i)
{
	while (i-- > 0)
		l = l->next;
	return (l);
}

void	ft_list_reverse_fun(t_list *begin_list)
{
	int		i;
	int		n;
	void	*tmp;
	t_list	*a;
	t_list	*b;

	n = list_len(begin_list);
	i = 0;
	while (i < n / 2)
	{
		a = list_at(begin_list, i);
		b = list_at(begin_list, n - 1 - i);
		tmp = a->data;
		a->data = b->data;
		b->data = tmp;
		i++;
	}
}
