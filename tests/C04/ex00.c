#include "t.h"
int	ft_strlen(char *str);
#define C(s) do { char x[] = s; t_int("ft_strlen(\"" s "\")", ft_strlen(x), strlen(x)); } while (0)
int	main(void){ C(""); C("a"); C("Hello"); C("42 Bangkok Piscine"); C("tab\there"); return (t_done()); }
