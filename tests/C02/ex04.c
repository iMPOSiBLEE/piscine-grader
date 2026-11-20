#include "t.h"
int	ft_str_is_lowercase(char *str);
static int	r(char *s){ while (*s) { unsigned char c = *s++; if (!(c >= 'a' && c <= 'z')) return 0; } return 1; }
#define C(s) do { char x[] = s; t_int("ft_str_is_lowercase(\"" s "\")", ft_str_is_lowercase(x), r(x)); } while (0)
int	main(void){ C(""); C("abc"); C("abC"); C("ab c"); C("z"); C("`{"); return (t_done()); }
