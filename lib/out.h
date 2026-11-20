#ifndef OUT_H
# define OUT_H
# include "t.h"
/* run CALL, capture stdout, compare with EXP */
# define T_OUT(NAME, CALL, EXP) do { char *g__; cap_start(); CALL; g__ = cap_end(); \
	t_str(NAME, g__, EXP); free(g__); } while (0)
#endif
