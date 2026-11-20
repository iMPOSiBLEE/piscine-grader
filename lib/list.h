#ifndef LIST_TEST_H
# define LIST_TEST_H
# include "t.h"
# include "ft_list.h"

/* ตัวตรวจใช้ ft_create_elem ของตัวเอง (weak) ถ้างานไม่ได้มีมาให้ */
__attribute__((weak)) t_list	*ft_create_elem(void *data)
{
	t_list	*e = malloc(sizeof(t_list));
	e->data = data;
	e->next = NULL;
	return (e);
}

static t_list	*L(int n, char **s)
{
	t_list	*b = NULL, **p = &b;
	for (int i = 0; i < n; i++) { *p = malloc(sizeof(t_list)); (*p)->data = s[i]; (*p)->next = NULL; p = &(*p)->next; }
	return (b);
}

static void	dump(char *o, t_list *l)
{
	int k = sprintf(o, "[");
	for (int i = 0; l && i < 100; l = l->next, i++) k += sprintf(o + k, "%s%s", i ? "," : "", l->data ? (char *)l->data : "NULL");
	sprintf(o + k, "]");
}
#endif
