#include "t.h"
char	*ft_strcpy(char *dest, char *src);
#define C(s) do { char d[64]; memset(d, 'Z', 63); d[63] = 0; char *r = ft_strcpy(d, s); \
	t_str("ft_strcpy(dest, \"" s "\")", d, s); t_ptr("  ค่าที่ return ต้องเป็น dest", r, d); } while (0)
int	main(void){ C("Hello"); C(""); C("42 Bangkok"); C("a"); return (t_done()); }
