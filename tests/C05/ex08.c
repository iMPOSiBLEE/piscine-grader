#include "t.h"
int	ft_ten_queens_puzzle(void);
static int	g_b[10];
static char	g_out[724 * 11 + 1];
static int	g_n = 0;
static int	ok(int c, int r){ for (int i = 0; i < c; i++) if (g_b[i] == r || abs(g_b[i] - r) == c - i) return 0; return 1; }
static void	solve(int c){ if (c == 10) { for (int i = 0; i < 10; i++) g_out[g_n * 11 + i] = '0' + g_b[i]; g_out[g_n * 11 + 10] = '\n'; g_n++; return; }
	for (int r = 0; r < 10; r++) if (ok(c, r)) { g_b[c] = r; solve(c + 1); } }
int	main(void)
{
	char	*got;
	int		ret;

	solve(0);
	cap_start();
	ret = ft_ten_queens_puzzle();
	got = cap_end();
	t_int("ft_ten_queens_puzzle() ค่าที่ return", ret, 724);
	if (strcmp(got, g_out) == 0)
		t_ok("ผลที่พิมพ์ออกมา 724 แบบ เรียงลำดับถูก");
	else
		t_ko("ผลที่พิมพ์ออกมา (ดู 3 บรรทัดแรก)", g_out, got);
	free(got);
	return (t_done());
}
