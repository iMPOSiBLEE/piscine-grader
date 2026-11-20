#include "t.h"
char	*ft_strstr(char *str, char *to_find);
#define C(h, n) do { char x[] = h; char y[] = n; t_ptr("ft_strstr(\"" h "\", \"" n "\")", ft_strstr(x, y), strstr(x, y)); } while (0)
int	main(void)
{
	C("Hello World", "World"); C("Hello World", "o"); C("Hello World", "xyz"); C("Hello", "");
	C("", ""); C("", "a"); C("aaab", "aab"); C("abc", "abcd"); C("ababc", "abc"); C("Bangkok", "kok");
	return (t_done());
}
