#include "t.h"
void	ft_ft(int *nbr);
int	main(void){ int n = 0; ft_ft(&n); t_int("ft_ft(&n) แล้ว n", n, 42); n = -7; ft_ft(&n); t_int("ft_ft(&n) จาก -7", n, 42); return (t_done()); }
