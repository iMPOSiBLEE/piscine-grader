#include "t.h"
char	*ft_convert_base(char *nbr, char *base_from, char *base_to);
static int	ok(char *b){ int n = strlen(b); if (n < 2) return 0; for (int i = 0; i < n; i++) { if (b[i] == '+' || b[i] == '-' || b[i] == ' ' || (b[i] >= 9 && b[i] <= 13)) return 0; for (int j = i + 1; j < n; j++) if (b[i] == b[j]) return 0; } return n; }
static int	idx(char c, char *b){ for (int i = 0; b[i]; i++) if (b[i] == c) return i; return -1; }
static char	*r(char *s, char *bf, char *bt, char *out)
{
	int nf = ok(bf), nt = ok(bt), sign = 1, d; long v = 0; char tmp[64]; int k = 0;
	if (!nf || !nt) return NULL;
	while (*s == ' ' || (*s >= 9 && *s <= 13)) s++;
	while (*s == '+' || *s == '-') { if (*s == '-') sign = -sign; s++; }
	while ((d = idx(*s, bf)) >= 0) { v = v * nf + d; s++; }
	v *= sign; char *o = out; if (v < 0) { *o++ = '-'; v = -v; }
	do { tmp[k++] = bt[v % nt]; v /= nt; } while (v);
	while (k) *o++ = tmp[--k]; *o = 0; return out;
}
#define C(n, f, t) do { char e[64]; char *w = r(n, f, t, e); char *g = ft_convert_base(n, f, t); \
	t_str("ft_convert_base(\"" n "\", \"" f "\", \"" t "\")", g, w); free(g); } while (0)
int	main(void)
{
	C("42", "0123456789", "01"); C("  ---+42", "0123456789", "01"); C("ff", "0123456789abcdef", "0123456789");
	C("-2147483648", "0123456789", "0123456789abcdef"); C("2147483647", "0123456789", "01"); C("0", "0123456789", "01");
	C("-0", "0123456789", "0123456789"); C("101010zz", "01", "poneyvif"); C("", "01", "0123456789");
	C("42", "0", "01"); C("42", "0123456789", "0"); C("42", "01-", "01"); C("42", "0123456789", "0110");
	return (t_done());
}
