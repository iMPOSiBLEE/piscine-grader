#include "btree.h"
int	btree_level_count(t_btree *root);
int	main(void)
{
	t_int("level_count(ต้นไม้ตัวอย่าง)", btree_level_count(sample()), 4);
	t_int("level_count(node เดียว)", btree_level_count(N("a", 0, 0)), 1);
	t_int("level_count(NULL)", btree_level_count(NULL), 0);
	t_int("level_count(เอียงซ้าย 3 ชั้น)", btree_level_count(N("a", N("b", N("c", 0, 0), 0), 0)), 3);
	return (t_done());
}
