#include "btree.h"
void	btree_apply_by_level(t_btree *root, void (*applyf)(void *item, int current_level, int is_first_elem));
static void	lv(void *item, int level, int first){ char b[32]; sprintf(b, "%s%s%d ", first ? "|" : "", (char *)item, level); strcat(g_out, b); }
int	main(void)
{
	g_out[0] = 0; btree_apply_by_level(sample(), &lv);
	t_str("ทีละชั้น (| = ตัวแรกของชั้น, ตัวเลข = level)", g_out, "|d0 |b1 f1 |a2 c2 e2 g2 |h3 ");
	g_out[0] = 0; btree_apply_by_level(NULL, &lv); t_str("root = NULL", g_out, "");
	return (t_done());
}
