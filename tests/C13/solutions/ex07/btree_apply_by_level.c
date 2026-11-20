#include "ft_btree.h"

int	level_count(t_btree *root)
{
	int	l;
	int	r;

	if (!root)
		return (0);
	l = level_count(root->left);
	r = level_count(root->right);
	if (l > r)
		return (l + 1);
	return (r + 1);
}

void	apply_level(t_btree *node, int target, int *first,
	void (*applyf)(void *, int, int))
{
	static int	depth;

	if (!node)
		return ;
	if (depth == target)
	{
		applyf(node->item, target, *first);
		*first = 0;
		return ;
	}
	depth++;
	apply_level(node->left, target, first, applyf);
	apply_level(node->right, target, first, applyf);
	depth--;
}

void	btree_apply_by_level(t_btree *root,
	void (*applyf)(void *item, int current_level, int is_first_elem))
{
	int	level;
	int	n;
	int	first;

	n = level_count(root);
	level = 0;
	while (level < n)
	{
		first = 1;
		apply_level(root, level, &first, applyf);
		level++;
	}
}
