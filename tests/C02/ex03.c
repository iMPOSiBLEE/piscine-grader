#include "t.h"
int	ft_str_is_numeric(char *str);
static int	r(char *s){ while (*s) { unsigned char c = *s++; if (!(c >= '0' && c <= '9')) return 0; } return 1; }
#define C(s) do { char x[] = s; t_int("ft_str_is_numeric(\"" s "\")", ft_str_is_numeric(x), r(x)); } while (0)
int	main(void){ C(""); C("0123456789"); C("12a"); C(" 1"); C("/:"); C("-1"); return (t_done()); }
