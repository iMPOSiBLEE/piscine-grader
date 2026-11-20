#include "t.h"
unsigned int	ft_strlcpy(char *dest, char *src, unsigned int size);
static unsigned int	r(char *d, char *s, unsigned int n){ unsigned int l = strlen(s), i = 0; if (n) { while (i < n - 1 && s[i]) { d[i] = s[i]; i++; } d[i] = 0; } return l; }
#define C(s, n) do { char g[32], e[32]; memset(g, 'Z', 31); memset(e, 'Z', 31); g[31] = e[31] = 0; \
	unsigned int a = ft_strlcpy(g, s, n); unsigned int b = r(e, s, n); \
	t_int("ft_strlcpy(dest, \"" s "\", " #n ") ค่าที่ return", a, b); t_str("  dest หลังเรียก", g, e); } while (0)
int	main(void){ C("Hello", 10); C("Hello", 6); C("Hello", 5); C("Hello", 1); C("Hello", 0); C("", 5); return (t_done()); }
