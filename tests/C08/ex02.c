#include "ft_abs.h"
#include "ft_abs.h"
#include "t.h"
#include <limits.h>
int	main(void)
{
	int x = -7;
	t_int("ABS(-5)", ABS(-5), 5); t_int("ABS(5)", ABS(5), 5); t_int("ABS(0)", ABS(0), 0);
	t_int("ABS(x) โดย x = -7", ABS(x), 7);
	t_int("ABS(2 - 5) (ต้องใส่วงเล็บรอบ Value)", ABS(2 - 5), 3);
	t_int("10 - ABS(-3) (ต้องใส่วงเล็บครอบทั้ง macro)", 10 - ABS(-3), 7);
	t_int("ABS(-3) * 2", ABS(-3) * 2, 6);
	t_int("ABS(INT_MAX)", ABS(INT_MAX), INT_MAX);
	return (t_done());
}
