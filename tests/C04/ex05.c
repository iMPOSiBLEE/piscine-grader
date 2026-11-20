#include "t.h"
int	ft_atoi_base(char *str, char *base);
static int	ok(char *b){ int n = strlen(b); if (n < 2) return 0; for (int i = 0; i < n; i++) { if (b[i] == '+' || b[i] == '-' || b[i] == ' ' || (b[i] >= 9 && b[i] <= 13)) return 0; for (int j = i + 1; j < n; j++) if (b[i] == b[j]) return 0; } return n; }
static int	idx(char c, char *b){ for (int i = 0; b[i]; i++) if (b[i] == c) return i; return -1; }
static int	r(char *s, char *b){ int n = ok(b), sign = 1, d; long v = 0; if (!n) return 0; while (*s == ' ' || (*s >= 9 && *s <= 13)) s++;
	while (*s == '+' || *s == '-') { if (*s == '-') sign = -sign; s++; } while ((d = idx(*s, b)) >= 0) { v = v * n + d; s++; } return (int)(v * sign); }
#define C(s, base) do { char x[] = s; char b[] = base; t_int("ft_atoi_base(\"" s "\", \"" base "\")", ft_atoi_base(x, b), r(x, b)); } while (0)
int	main(void)
{
	C("42", "0123456789"); C("101010", "01"); C("ff", "0123456789abcdef"); C("FF", "0123456789abcdef"); C("  -+-2a", "0123456789abcdef");
	C("-2147483648", "0123456789"); C("2147483647", "0123456789"); C("vn", "poneyvif"); C("12x3", "0123456789");
	C("42", ""); C("42", "1"); C("42", "0123456789+"); C("42", "01 23"); C("42", "0112"); C("", "01");
	return (t_done());
}
