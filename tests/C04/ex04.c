#include "out.h"
#include <limits.h>
void	ft_putnbr_base(int nbr, char *base);
static int	ok(char *b){ int n = strlen(b); if (n < 2) return 0; for (int i = 0; i < n; i++) { if (b[i] == '+' || b[i] == '-') return 0; for (int j = i + 1; j < n; j++) if (b[i] == b[j]) return 0; } return n; }
static void	rec(char **o, long v, char *b, int n){ if (v >= n) rec(o, v / n, b, n); *(*o)++ = b[v % n]; }
static void	r(char *o, int nbr, char *b){ int n = ok(b); long v = nbr; if (!n) { *o = 0; return; } if (v < 0) { *o++ = '-'; v = -v; } rec(&o, v, b, n); *o = 0; }
#define C(v, base) do { char b[] = base; char e[128]; r(e, v, b); T_OUT("ft_putnbr_base(" #v ", \"" base "\")", ft_putnbr_base(v, b), e); } while (0)
int	main(void)
{
	C(42, "0123456789"); C(42, "01"); C(255, "0123456789ABCDEF"); C(-255, "0123456789abcdef"); C(42, "poneyvif");
	C(0, "01"); C(INT_MIN, "0123456789"); C(INT_MAX, "01"); C(INT_MIN, "0123456789abcdef");
	C(42, ""); C(42, "0"); C(42, "0120"); C(42, "01+"); C(42, "-01");
	return (t_done());
}
