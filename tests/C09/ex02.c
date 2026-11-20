#include "t.h"
char	**ft_split(char *str, char *charset);
static void	join(char *o, char **t){ int k = sprintf(o, "["); if (!t) { strcpy(o, "NULL"); return; }
	for (int i = 0; t[i]; i++) k += sprintf(o + k, "%s\"%s\"", i ? ", " : "", t[i]); sprintf(o + k, ", 0]"); }
static void	r(char *o, char *s, char *cs){ int k = sprintf(o, "["), first = 1;
	while (*s) { while (*s && strchr(cs, *s) && *cs) s++; if (!*s) break; char *st = s; while (*s && !(*cs && strchr(cs, *s))) s++;
		k += sprintf(o + k, "%s\"%.*s\"", first ? "" : ", ", (int)(s - st), st); first = 0; } sprintf(o + k, first ? "0]" : ", 0]"); }
static void	fix(char *o){ char *p = strstr(o, "[, 0]"); if (p) memmove(p + 1, p + 3, strlen(p + 3) + 1); }
#define C(s, cs) do { char x[] = s; char w[1024], g[1024]; char **t = ft_split(x, cs); r(w, x, cs); join(g, t); fix(g); \
	t_str("ft_split(" #s ", " #cs ")", g, w); if (t) { for (int i = 0; t[i]; i++) free(t[i]); free(t); } } while (0)
int	main(void)
{
	C("Hello World 42", " "); C("   lots   of   spaces   ", " "); C("a,b;;c,,d", ",;"); C("nosep", " ");
	C("", " "); C("     ", " "); C("abc", ""); C("x", "x"); C("1a2b3", "abc"); C("\ttab\nnew line", " \t\n");
	return (t_done());
}
