#include "t.h"
char	*ft_strjoin(int size, char **strs, char *sep);
static void	c(const char *name, int size, char **strs, char *sep)
{
	char e[512] = ""; char *g;
	for (int i = 0; i < size; i++) { if (i) strcat(e, sep); strcat(e, strs[i]); }
	g = ft_strjoin(size, strs, sep); t_str(name, g, e); free(g);
}
int	main(void)
{
	char *a[] = {"Hello", "World", "42"}; char *b[] = {"one"}; char *d[] = {"", "x", ""};
	c("ft_strjoin(3, {Hello,World,42}, \", \")", 3, a, ", ");
	c("ft_strjoin(3, ..., \"\") sep ว่าง", 3, a, "");
	c("ft_strjoin(1, {one}, \"-\")", 1, b, "-");
	c("ft_strjoin(3, {\"\",x,\"\"}, \"|\")", 3, d, "|");
	c("ft_strjoin(0, ...) ต้องได้ \"\" ที่ free ได้", 0, a, "-");
	return (t_done());
}
