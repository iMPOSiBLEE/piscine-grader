#include "t.h"
int	ft_any(char **tab, int (*f)(char *));
static int	has_a(char *s){ return strchr(s, 'a') != NULL; }
static int	g_calls;
static int	cnt(char *s){ g_calls++; return s[0] == 'x'; }
int	main(void)
{
	char *a[] = {"hello", "world", "abc", 0}; char *b[] = {"hello", "world", 0}; char *c[] = {0};
	t_int("ft_any({hello, world, abc}, มีตัว a)", ft_any(a, &has_a), 1);
	t_int("ft_any({hello, world}, มีตัว a)", ft_any(b, &has_a), 0);
	t_int("ft_any({}, ...) array ว่าง", ft_any(c, &has_a), 0);
	char *d[] = {"x1", "x2", "x3", 0}; g_calls = 0; ft_any(d, &cnt);
	t_int("ต้องหยุดทันทีเมื่อเจอตัวแรก (เรียก f กี่ครั้ง)", g_calls, 1);
	return (t_done());
}
