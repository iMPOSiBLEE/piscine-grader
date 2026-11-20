#include <unistd.h>

int	is_safe(int *board, int col, int row)
{
	int	c;
	int	diff;

	c = 0;
	while (c < col)
	{
		if (board[c] == row)
			return (0);
		diff = board[c] - row;
		if (diff < 0)
			diff = -diff;
		if (diff == col - c)
			return (0);
		c++;
	}
	return (1);
}

void	print_board(int *board)
{
	int		i;
	char	c;

	i = 0;
	while (i < 10)
	{
		c = board[i] + '0';
		write(1, &c, 1);
		i++;
	}
	write(1, "\n", 1);
}

void	solve(int *board, int col, int *count)
{
	int	row;

	if (col == 10)
	{
		print_board(board);
		*count = *count + 1;
		return ;
	}
	row = 0;
	while (row < 10)
	{
		if (is_safe(board, col, row))
		{
			board[col] = row;
			solve(board, col + 1, count);
		}
		row++;
	}
}

int	ft_ten_queens_puzzle(void)
{
	int	board[10];
	int	count;

	count = 0;
	solve(board, 0, &count);
	return (count);
}
