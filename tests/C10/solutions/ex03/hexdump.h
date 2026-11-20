#ifndef HEXDUMP_H
# define HEXDUMP_H

typedef struct s_hd
{
	unsigned char	line[16];
	unsigned char	prev[16];
	int				len;
	int				has_prev;
	int				star;
	unsigned long	off;
}	t_hd;

#endif
