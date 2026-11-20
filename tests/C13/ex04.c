#include "btree.h"
void	btree_insert_data(t_btree **root, void *item, int (*cmpf)(void *, void *));
void	inf(t_btree *r){ if (!r) return; inf(r->left); strcat(g_out, (char *)r->item); inf(r->right); }
int	main(void)
{
	t_btree *root = NULL; char *v[] = {"m", "c", "x", "a", "e", "z", "m", "b"};
	for (int i = 0; i < 8; i++) btree_insert_data(&root, v[i], &scmp);
	t_ptr("ตัวแรกต้องเป็น root", root ? root->item : NULL, v[0]);
	g_out[0] = 0; inf(root); t_str("infix หลังใส่ครบต้องเรียงลำดับ", g_out, "abcemmxz");
	t_ptr("ค่าที่เท่ากันต้องไปทางขวา", root && root->right && root->right->left ? root->right->left->item : NULL, v[6]);
	return (t_done());
}
