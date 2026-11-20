#include "t.h"
#include <limits.h>
void	ft_swap(int *a, int *b);
int	main(void)
{
	int a = 1, b = 2; ft_swap(&a, &b); t_int("swap(1,2) → a", a, 2); t_int("swap(1,2) → b", b, 1);
	a = INT_MIN; b = INT_MAX; ft_swap(&a, &b); t_int("swap(INT_MIN,INT_MAX) → a", a, INT_MAX); t_int("swap(INT_MIN,INT_MAX) → b", b, INT_MIN);
	a = 5; b = 5; ft_swap(&a, &b); t_int("swap(5,5) → a", a, 5);
	return (t_done());
}
