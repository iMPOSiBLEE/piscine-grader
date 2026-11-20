/* Test helpers: each test prints one line per case and exits 1 if any case fails. */
#ifndef T_H
# define T_H
# include <stdio.h>
# include <string.h>
# include <stdlib.h>
# include <unistd.h>

static int	g_fail = 0;
static int	g_total = 0;

# define SHOWMAX 200

static void	t_ok(const char *name)
{
	g_total++;
	printf("  \033[32m✔\033[0m %s\n", name);
}

static void	t_ko(const char *name, const char *exp, const char *got)
{
	g_total++;
	g_fail++;
	printf("  \033[31m✘ %s\033[0m\n      ควรได้: %.*s\n      ได้จริง: %.*s\n",
		name, SHOWMAX, exp, SHOWMAX, got);
}

static void	t_int(const char *name, long got, long exp)
{
	char	a[64];
	char	b[64];

	if (got == exp)
		return (t_ok(name));
	snprintf(a, sizeof a, "%ld", exp);
	snprintf(b, sizeof b, "%ld", got);
	t_ko(name, a, b);
}

static int	t_sign(long v)
{
	return ((v > 0) - (v < 0));
}

/* compare only the sign (<0, 0, >0), like strcmp results */
static void	t_cmp(const char *name, long got, long exp)
{
	char	a[64];
	char	b[64];

	if (t_sign(got) == t_sign(exp))
		return (t_ok(name));
	snprintf(a, sizeof a, "%s (%ld)", exp < 0 ? "ติดลบ" : exp > 0 ? "บวก" : "0", exp);
	snprintf(b, sizeof b, "%s (%ld)", got < 0 ? "ติดลบ" : got > 0 ? "บวก" : "0", got);
	t_ko(name, a, b);
}

static void	t_str(const char *name, const char *got, const char *exp)
{
	char	a[512];
	char	b[512];

	if ((got == NULL && exp == NULL) || (got && exp && strcmp(got, exp) == 0))
		return (t_ok(name));
	snprintf(a, sizeof a, exp ? "\"%s\"" : "%s", exp ? exp : "NULL");
	snprintf(b, sizeof b, got ? "\"%s\"" : "%s", got ? got : "NULL");
	t_ko(name, a, b);
}

static void	t_ptr(const char *name, const void *got, const void *exp)
{
	char	a[64];
	char	b[64];

	if (got == exp)
		return (t_ok(name));
	snprintf(a, sizeof a, "%p", exp);
	snprintf(b, sizeof b, "%p", got);
	t_ko(name, a, b);
}

/* ---- capture what a function writes to stdout (fd 1) ---- */
static int	g_saved = -1;
static FILE	*g_cap = NULL;

static void	cap_start(void)
{
	fflush(stdout);
	g_cap = tmpfile();
	g_saved = dup(1);
	dup2(fileno(g_cap), 1);
}

/* returns malloc'd string of everything written since cap_start */
static char	*cap_end(void)
{
	long	n;
	char	*buf;

	fflush(stdout);
	dup2(g_saved, 1);
	close(g_saved);
	n = lseek(fileno(g_cap), 0, SEEK_END);
	if (n < 0)
		n = 0;
	buf = calloc(n + 1, 1);
	lseek(fileno(g_cap), 0, SEEK_SET);
	if (n > 0 && read(fileno(g_cap), buf, n) != n)
		buf[0] = '\0';
	fclose(g_cap);
	return (buf);
}

static int	t_done(void)
{
	printf("  ── %d/%d เคสผ่าน\n", g_total - g_fail, g_total);
	return (g_fail ? 1 : 0);
}
#endif
