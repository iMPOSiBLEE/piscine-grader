#include "list.h"
t_list	*ft_list_find(t_list *begin_list, void *data_ref, int (*cmp)());
static int	cmp(void *a, void *b){ return strcmp((char *)a, (char *)b); }
int	main(void)
{
	char *s[] = {"a", "b", "c", "b"}; t_list *l = L(4, s);
	t_ptr("find(\"b\") ต้องได้ตัวแรกที่เจอ", ft_list_find(l, "b", &cmp), l->next);
	t_ptr("find(\"z\") ไม่เจอ ต้อง NULL", ft_list_find(l, "z", &cmp), NULL);
	t_ptr("find ใน list ว่าง", ft_list_find(NULL, "a", &cmp), NULL);
	return (t_done());
}
