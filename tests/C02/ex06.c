#include "t.h"
int	ft_str_is_printable(char *str);
static int	r(char *s){ while (*s) { unsigned char c = *s++; if (!(c >= 32 && c <= 126)) return 0; } return 1; }
#define C(s) do { char x[] = s; t_int("ft_str_is_printable(\"" s "\")", ft_str_is_printable(x), r(x)); } while (0)
int	main(void){ C(""); C("Hello World!"); C("~ "); C("tab\there"); C("new\nline"); C("\177"); C("\200"); return (t_done()); }
