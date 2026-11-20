#include "t.h"
int	ft_is_sort(int *tab, int length, int (*f)(int, int));
static int	cmp(int a, int b){ return a - b; }
#define C(name, exp, ...) do { int t[] = {__VA_ARGS__}; t_int(name, ft_is_sort(t, sizeof(t) / sizeof(int), &cmp), exp); } while (0)
int	main(void)
{
	C("{1, 2, 3, 4} เรียงจากน้อยไปมาก", 1, 1, 2, 3, 4);
	C("{4, 3, 2, 1} เรียงจากมากไปน้อย (นับว่าเรียง)", 1, 4, 3, 2, 1);
	C("{1, 3, 2} ไม่เรียง", 0, 1, 3, 2);
	C("{2, 2, 2} เท่ากันหมด", 1, 2, 2, 2);
	C("{1, 1, 2, 2, 3}", 1, 1, 1, 2, 2, 3);
	C("{5} ตัวเดียว", 1, 5);
	C("{3, 1, 2}", 0, 3, 1, 2);
	{ int t[] = {1}; t_int("length 0", ft_is_sort(t, 0, &cmp), 1); }
	return (t_done());
}
