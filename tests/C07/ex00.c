#include "t.h"
char	*ft_strdup(char *src);
#define C(s) do { char x[] = s; char *d = ft_strdup(x); t_str("ft_strdup(\"" s "\")", d, s); \
	if (d == x) t_ko("  ต้อง malloc ที่ใหม่ ไม่ใช่คืน src เดิม", "pointer ใหม่", "pointer เดียวกับ src"); else t_ok("  ได้ pointer ใหม่ (malloc)"); free(d); } while (0)
int	main(void){ C("Hello"); C(""); C("42 Bangkok Piscine"); return (t_done()); }
