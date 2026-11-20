#include "t.h"
unsigned int	ft_strlcat(char *dest, char *src, unsigned int size);
static unsigned int	r(char *d, char *s, unsigned int size)
{
	unsigned int dl = 0, sl = strlen(s), i = 0;
	while (dl < size && d[dl]) dl++;
	if (dl == size) return (size + sl);
	while (s[i] && dl + i + 1 < size) { d[dl + i] = s[i]; i++; }
	d[dl + i] = '\0';
	return (dl + sl);
}
#define C(d, s, n) do { char x[64]; char e[64]; memset(x, 'Z', 63); memset(e, 'Z', 63); x[63] = e[63] = 0; strcpy(x, d); strcpy(e, d); \
	unsigned int g = ft_strlcat(x, s, n); unsigned int w = r(e, s, n); \
	t_int("ft_strlcat(\"" d "\", \"" s "\", " #n ") ค่าที่ return", g, w); t_str("  dest หลังเรียก", x, e); } while (0)
int	main(void)
{
	C("Hello ", "World", 20); C("Hello ", "World", 9); C("Hello ", "World", 7); C("Hello ", "World", 6);
	C("Hello ", "World", 3); C("Hello ", "World", 0); C("", "abc", 4); C("", "abc", 1); C("abc", "", 10);
	return (t_done());
}
