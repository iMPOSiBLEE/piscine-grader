#include "t.h"
char	*ft_strcat(char *dest, char *src);
#define C(d, s) do { char x[64] = d; char e[64] = d; char *ret = ft_strcat(x, s); strcat(e, s); \
	t_str("ft_strcat(\"" d "\", \"" s "\")", x, e); t_ptr("  ค่าที่ return ต้องเป็น dest", ret, x); } while (0)
int	main(void)
{
	C("Hello ", "World"); C("", "abc"); C("abc", ""); C("", ""); C("42", " Bangkok Piscine");
	return (t_done());
}
