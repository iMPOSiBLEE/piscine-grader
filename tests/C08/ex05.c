#include "ft_stock_str.h"
#include "out.h"
void	ft_show_tab(struct s_stock_str *par);
int	main(void)
{
	char s0[] = "Hello", s1[] = "", s2[] = "42 Bangkok", c0[] = "Hello", c1[] = "", c2[] = "copy!";
	t_stock_str t[] = {{5, s0, c0}, {0, s1, c1}, {10, s2, c2}, {2147483647, s0, c0}, {0, 0, 0}};
	T_OUT("ft_show_tab(4 ช่อง)", ft_show_tab(t), "Hello\n5\nHello\n\n0\n\n42 Bangkok\n10\ncopy!\nHello\n2147483647\nHello\n");
	T_OUT("ft_show_tab(array ว่าง)", ft_show_tab(t + 4), "");
	return (t_done());
}
