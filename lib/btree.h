#ifndef BTREE_TEST_H
# define BTREE_TEST_H
# include "t.h"
# include "ft_btree.h"

__attribute__((weak)) t_btree	*btree_create_node(void *item)
{
	t_btree	*n = malloc(sizeof(t_btree));
	n->item = item;
	n->left = NULL;
	n->right = NULL;
	return (n);
}

static t_btree	*N(char *s, t_btree *l, t_btree *r)
{
	t_btree	*n = malloc(sizeof(t_btree));
	n->item = s; n->left = l; n->right = r;
	return (n);
}

/*        d
 *      /   \
 *     b     f
 *    / \   / \
 *   a   c e   g
 *              \
 *               h          */
static t_btree	*sample(void)
{
	return (N("d", N("b", N("a", 0, 0), N("c", 0, 0)), N("f", N("e", 0, 0), N("g", 0, N("h", 0, 0)))));
}

static char	g_out[512];
static void	rec(void *item){ strcat(g_out, (char *)item); }
static int	scmp(void *a, void *b){ return strcmp((char *)a, (char *)b); }
#endif
