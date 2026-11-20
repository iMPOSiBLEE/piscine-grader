#include "list.h"
t_list	*ft_create_elem(void *data);
int	main(void)
{
	char s[] = "42"; t_list *e = ft_create_elem(s);
	if (!e) { t_ko("ft_create_elem(\"42\")", "element", "NULL"); return (t_done()); }
	t_ptr("data ต้องชี้ไปที่ค่าที่ส่งมา", e->data, s); t_ptr("next ต้องเป็น NULL", e->next, NULL);
	t_list *z = ft_create_elem(NULL); t_ptr("ft_create_elem(NULL) data = NULL", z ? z->data : (void *)1, NULL);
	return (t_done());
}
