#include "t.h"
int	ft_str_is_alpha(char *str);
static int	r(char *s){ while (*s) { unsigned char c = *s++; if (!((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z'))) return 0; } return 1; }
#define C(s) do { char x[] = s; t_int("ft_str_is_alpha(\"" s "\")", ft_str_is_alpha(x), r(x)); } while (0)
int	main(void){ C(""); C("abc"); C("ABCxyz"); C("abc1"); C("a b"); C("Zz"); C("!"); C("@[`{"); return (t_done()); }
