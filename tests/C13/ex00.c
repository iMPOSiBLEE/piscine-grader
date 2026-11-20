#include "btree.h"
t_btree	*btree_create_node(void *item);
int	main(void)
{
	char s[] = "42"; t_btree *n = btree_create_node(s);
	if (!n) { t_ko("btree_create_node(\"42\")", "node", "NULL"); return (t_done()); }
	t_ptr("item ต้องเป็นค่าที่ส่งมา", n->item, s); t_ptr("left = NULL", n->left, NULL); t_ptr("right = NULL", n->right, NULL);
	return (t_done());
}
