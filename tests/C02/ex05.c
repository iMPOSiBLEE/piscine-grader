#include "t.h"
int	ft_str_is_uppercase(char *str);
static int	r(char *s){ while (*s) { unsigned char c = *s++; if (!(c >= 'A' && c <= 'Z')) return 0; } return 1; }
#define C(s) do { char x[] = s; t_int("ft_str_is_uppercase(\"" s "\")", ft_str_is_uppercase(x), r(x)); } while (0)
int	main(void){ C(""); C("ABC"); C("ABc"); C("AB C"); C("Z"); C("@["); return (t_done()); }
