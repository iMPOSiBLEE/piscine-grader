#include "t.h"
char	*ft_strlowcase(char *str);
static void	r(char *s){ for (; *s; s++) if (*s >= 'A' && *s <= 'Z') *s += 32; }
#define C(s) do { char x[] = s; char e[] = s; r(e); char *ret = ft_strlowcase(x); t_str("ft_strlowcase(\"" s "\")", x, e); t_ptr("  ค่าที่ return ต้องเป็น str", ret, x); } while (0)
int	main(void){ C("Hello World 42!"); C(""); C("abcxyz"); C("ABCXYZ"); C("@[`{"); return (t_done()); }
