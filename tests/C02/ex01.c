#include "t.h"
char	*ft_strncpy(char *dest, char *src, unsigned int n);
static void	hex(char *o, char *b, int n){ int k = 0; for (int i = 0; i < n; i++) k += sprintf(o + k, "%s", b[i] == 0 ? "\\0" : (char[]){b[i], 0}); }
#define C(s, n) do { char g[32], e[32], hg[128], he[128]; memset(g, 'Z', 32); memset(e, 'Z', 32); \
	char *r = ft_strncpy(g, s, n); strncpy(e, s, n); hex(hg, g, 12); hex(he, e, 12); \
	t_str("ft_strncpy(dest, \"" s "\", " #n ") (12 ช่องแรก, ต้องเติม \\0 ให้ครบ n)", hg, he); t_ptr("  ค่าที่ return ต้องเป็น dest", r, g); } while (0)
int	main(void){ C("Hello", 3); C("Hello", 5); C("Hello", 8); C("Hello", 0); C("", 4); C("abc", 10); return (t_done()); }
