#include "list.h"
t_list	*ft_list_push_strs(int size, char **strs);
int	main(void)
{
	char *s[] = {"one", "two", "three"}; char g[256];
	dump(g, ft_list_push_strs(3, s)); t_str("push_strs(3, {one,two,three}) ตัวแรกต้องอยู่ท้าย", g, "[three,two,one]");
	dump(g, ft_list_push_strs(1, s)); t_str("push_strs(1, ...)", g, "[one]");
	t_ptr("push_strs(0, ...) ต้องได้ NULL", ft_list_push_strs(0, s), NULL);
	return (t_done());
}
