#include "ft.h"
#include "ft.h"
#include "t.h"
/* ถ้า prototype ใน ft.h ไม่ตรงโจทย์ บรรทัดด้านล่างจะคอมไพล์ไม่ผ่าน (conflicting types) */
void	ft_putchar(char c){ (void)c; }
void	ft_swap(int *a, int *b){ int t = *a; *a = *b; *b = t; }
void	ft_putstr(char *str){ (void)str; }
int	ft_strlen(char *str){ return ((int)strlen(str)); }
int	ft_strcmp(char *s1, char *s2){ return (strcmp(s1, s2)); }
int	main(void)
{
	void (*a)(char) = ft_putchar; void (*b)(int *, int *) = ft_swap; void (*c)(char *) = ft_putstr;
	int (*d)(char *) = ft_strlen; int (*e)(char *, char *) = ft_strcmp;
	(void)a; (void)b; (void)c; (void)d; (void)e;
	t_ok("ft.h มี prototype ครบ 5 ตัว ตรงตามโจทย์ และ include ซ้ำได้");
	return (t_done());
}
