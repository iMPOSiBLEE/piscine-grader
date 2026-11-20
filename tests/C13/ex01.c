#include "btree.h"
void	btree_apply_prefix(t_btree *root, void (*applyf)(void *));
int	main(void)
{
	g_out[0] = 0; btree_apply_prefix(sample(), &rec); t_str("prefix traversal ของต้นไม้ตัวอย่าง", g_out, "dbacfegh");
	g_out[0] = 0; btree_apply_prefix(N("x", 0, 0), &rec); t_str("node เดียว", g_out, "x");
	g_out[0] = 0; btree_apply_prefix(NULL, &rec); t_str("root = NULL ไม่เรียก applyf", g_out, "");
	return (t_done());
}
