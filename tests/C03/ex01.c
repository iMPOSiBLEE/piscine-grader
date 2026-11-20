#include "t.h"
int	ft_strncmp(char *s1, char *s2, unsigned int n);
static int	r(char *a, char *b, unsigned int n){ unsigned int i = 0; if (!n) return 0; while (i < n - 1 && a[i] && a[i] == b[i]) i++; return ((unsigned char)a[i] - (unsigned char)b[i]); }
#define C(a, b, n) do { char x[] = a; char y[] = b; t_cmp("ft_strncmp(\"" a "\", \"" b "\", " #n ")", ft_strncmp(x, y, n), r(x, y, n)); } while (0)
int	main(void)
{
	C("abc", "abc", 3); C("abc", "abd", 3); C("abc", "abd", 2); C("abd", "abc", 5);
	C("abc", "xyz", 0); C("", "", 1); C("", "a", 1); C("a", "", 1);
	C("Hello", "Help", 3); C("Hello", "Help", 4); C("ab", "abc", 10); C("abc", "ab", 3);
	return (t_done());
}
