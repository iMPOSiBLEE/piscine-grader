#include "out.h"
void	ft_putstr_non_printable(char *str);
static void	r(char *o, char *s){ for (; *s; s++) { unsigned char c = *s; if (c >= 32 && c <= 126) *o++ = c; else o += sprintf(o, "\\%02x", c); } *o = 0; }
#define C(s) do { char x[] = s; char e[256]; r(e, x); T_OUT("ft_putstr_non_printable(" #s ")", ft_putstr_non_printable(x), e); } while (0)
int	main(void)
{
	C("Coucou\ntu vas bien ?"); C(""); C("abc"); C("\t\v\r\033"); C("\177 del"); C("\200\377 (เกิน 127 ต้องเป็น \\80 \\ff)"); C("\x01\x1f");
	return (t_done());
}
