#include "list.h"
void	ft_list_remove_if(t_list **begin_list, void *data_ref, int (*cmp)(), void (*free_fct)(void *));
static int g_n;
static int	cmp(void *a, void *b){ return strcmp((char *)a, (char *)b); }
static void	fr(void *d){ g_n++; free(d); }
static t_list	*mk(const char *csv){ char *s[16]; int n = 0; char buf[64]; strcpy(buf, csv); for (char *t = strtok(buf, ","); t; t = strtok(NULL, ",")) s[n++] = strdup(t); return L(n, s); }
int	main(void)
{
	char g[256]; t_list *l;
	g_n = 0; l = mk("x,a,x,b,x"); ft_list_remove_if(&l, "x", &cmp, &fr); dump(g, l);
	t_str("remove_if(\"x\") จาก [x,a,x,b,x]", g, "[a,b]"); t_int("  free_fct ถูกเรียก 3 ครั้ง", g_n, 3);
	g_n = 0; l = mk("x,x"); ft_list_remove_if(&l, "x", &cmp, &fr); t_ptr("ลบหมดทุกตัว begin ต้องเป็น NULL", l, NULL);
	g_n = 0; l = mk("a,b"); ft_list_remove_if(&l, "q", &cmp, &fr); dump(g, l); t_str("ไม่มีตัวที่ตรง", g, "[a,b]");
	l = NULL; ft_list_remove_if(&l, "q", &cmp, &fr); t_ok("list ว่างไม่พัง");
	return (t_done());
}
