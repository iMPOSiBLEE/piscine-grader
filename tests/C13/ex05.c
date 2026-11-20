#include "btree.h"
void	*btree_search_item(t_btree *root, void *data_ref, int (*cmpf)(void *, void *));
int	main(void)
{
	t_btree *t = sample();
	char *r = btree_search_item(t, "e", &scmp); t_str("search(\"e\")", r, "e");
	t_ptr("search(\"q\") ไม่เจอต้อง NULL", btree_search_item(t, "q", &scmp), NULL);
	t_ptr("search ใน NULL", btree_search_item(NULL, "a", &scmp), NULL);
	char x1[] = "k", x2[] = "k";
	t_btree *dup = N(x1, N(x2, 0, 0), 0);
	t_ptr("มีค่าซ้ำ ต้องได้ตัวแรกตาม infix (ซ้ายก่อน)", btree_search_item(dup, "k", &scmp), x2);
	return (t_done());
}
