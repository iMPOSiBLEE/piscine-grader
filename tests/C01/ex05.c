#include "out.h"
void	ft_putstr(char *str);
#define P(s) do { char x[] = s; T_OUT("ft_putstr(" #s ")", ft_putstr(x), s); } while (0)
int	main(void){ P("Hello World"); P(""); P("a"); P("42\nBangkok\t!"); return (t_done()); }
