#include "ft_boolean.h"
#include "ft_boolean.h"
#include "t.h"
/* main ของโจทย์ แปลงเป็นฟังก์ชันเพื่อทดสอบหลายค่า argc */
static void	ft_putstr2(char *str){ while (*str) write(1, str++, 1); }
t_bool	ft_is_even(int nbr){ return ((EVEN(nbr)) ? TRUE : FALSE); }
static int	subject_main(int argc){ if (ft_is_even(argc - 1) == TRUE) ft_putstr2(EVEN_MSG); else ft_putstr2(ODD_MSG); return (SUCCESS); }
int	main(void)
{
	char *g; int ret = -1;
	for (int argc = 1; argc <= 4; argc++)
	{
		char name[80];
		cap_start(); ret = subject_main(argc); g = cap_end();
		snprintf(name, 80, "main ของโจทย์ เมื่อมี argument %d ตัว", argc - 1);
		t_str(name, g, (argc - 1) % 2 == 0 ? "I have an even number of arguments.\n" : "I have an odd number of arguments.\n");
		free(g);
	}
	t_int("SUCCESS ต้องเป็น 0", ret, 0);
	t_int("EVEN(-4)", EVEN(-4) ? 1 : 0, 1);
	t_int("EVEN(2 + 1) (ต้องใส่วงเล็บใน macro)", EVEN(2 + 1) ? 1 : 0, 0);
	return (t_done());
}
