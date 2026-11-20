#include "t.h"
char	*ft_strncat(char *dest, char *src, unsigned int nb);
#define C(d, s, n) do { char x[64]; char e[64]; memset(x, 'Z', 64); memset(e, 'Z', 64); strcpy(x, d); strcpy(e, d); \
	char *ret = ft_strncat(x, s, n); strncat(e, s, n); \
	t_str("ft_strncat(\"" d "\", \"" s "\", " #n ")", x, e); t_ptr("  ค่าที่ return ต้องเป็น dest", ret, x); } while (0)
int	main(void)
{
	C("Hello ", "World", 5); C("Hello ", "World", 3); C("Hello ", "World", 0); C("Hello ", "World", 20);
	C("", "abc", 2); C("abc", "", 4);
	return (t_done());
}
