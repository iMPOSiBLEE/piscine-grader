#include "t.h"
int	ft_strcmp(char *s1, char *s2);
static int	r(char *a, char *b){ while (*a && *a == *b) { a++; b++; } return ((unsigned char)*a - (unsigned char)*b); }
#define C(a, b) do { char x[] = a; char y[] = b; t_cmp("ft_strcmp(\"" a "\", \"" b "\")", ft_strcmp(x, y), r(x, y)); } while (0)
int	main(void)
{
	C("abc", "abc"); C("abc", "abd"); C("abd", "abc"); C("", ""); C("", "a"); C("a", "");
	C("abc", "ab"); C("ab", "abc"); C("Hello", "hello"); C("42", "42 Bangkok");
	{ char x[] = "a\200"; char y[] = "a"; t_cmp("ตัวอักษรเกิน 127 (unsigned char)", ft_strcmp(x, y), r(x, y)); }
	return (t_done());
}
