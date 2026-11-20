#include "t.h"
char	*ft_strcapitalize(char *str);
static int	an(char c){ return (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9'); }
static void	r(char *s){ for (int i = 0; s[i]; i++) { if (i == 0 || !an(s[i - 1])) { if (s[i] >= 'a' && s[i] <= 'z') s[i] -= 32; } else if (s[i] >= 'A' && s[i] <= 'Z') s[i] += 32; } }
#define C(s) do { char x[] = s; char e[] = s; r(e); char *ret = ft_strcapitalize(x); t_str("ft_strcapitalize(\"" s "\")", x, e); t_ptr("  ค่าที่ return ต้องเป็น str", ret, x); } while (0)
int	main(void)
{
	C("salut, comment tu vas ? 42mots quarante-deux; cinquante+et+un");
	C("HELLO WORLD"); C(""); C("a"); C("hELLO wORLD"); C("42abc ABC42 x"); C("  multiple   spaces");
	return (t_done());
}
