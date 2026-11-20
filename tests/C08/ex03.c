#include "ft_point.h"
#include "ft_point.h"
#include "t.h"
void	set_point(t_point *point){ point->x = 42; point->y = 21; }
int	main(void)
{
	t_point point;
	set_point(&point);
	t_int("main ของโจทย์คอมไพล์ได้ แล้ว point.x", point.x, 42);
	t_int("point.y", point.y, 21);
	return (t_done());
}
