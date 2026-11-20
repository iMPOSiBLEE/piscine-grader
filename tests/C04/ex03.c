#include "t.h"
int	ft_atoi(char *str);
static int	r(char *s){ int sign = 1; long v = 0; while (*s == ' ' || (*s >= 9 && *s <= 13)) s++;
	while (*s == '+' || *s == '-') { if (*s == '-') sign = -sign; s++; } while (*s >= '0' && *s <= '9') v = v * 10 + (*s++ - '0'); return (int)(v * sign); }
#define C(s) do { char x[] = s; t_int("ft_atoi(\"" s "\")", ft_atoi(x), r(x)); } while (0)
int	main(void)
{
	C(" ---+--+1234ab567"); C("42"); C("-42"); C("+42"); C("--42"); C("   \t\n\v\f\r 7"); C("abc"); C("");
	C("0"); C("-0"); C("2147483647"); C("-2147483648"); C("12 34"); C("+-+5"); C("- 5");
	return (t_done());
}
