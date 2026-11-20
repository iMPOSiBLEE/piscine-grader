#include "out.h"
void	*ft_print_memory(void *addr, unsigned int size);
static void	r(char *o, unsigned char *p, unsigned int size)
{
	for (unsigned int pos = 0; pos < size; pos += 16)
	{
		unsigned int n = size - pos > 16 ? 16 : size - pos;
		o += sprintf(o, "%016lx: ", (unsigned long)(p + pos));
		for (unsigned int i = 0; i < 16; i++) { if (i < n) o += sprintf(o, "%02x", p[pos + i]); else o += sprintf(o, "  "); if (i % 2) *o++ = ' '; }
		for (unsigned int i = 0; i < n; i++) *o++ = (p[pos + i] >= 32 && p[pos + i] <= 126) ? p[pos + i] : '.';
		*o++ = '\n';
	}
	*o = 0;
}
#define C(NAME, BUF, N) do { char e[4096]; void *ret; r(e, (unsigned char *)(BUF), N); \
	T_OUT(NAME, ret = ft_print_memory(BUF, N), e); t_ptr("  ค่าที่ return ต้องเป็น addr", ret, BUF); } while (0)
int	main(void)
{
	char	s[] = "Bonjour les aminches\t\n\tc\a est fou\ttout\tce qu on peut faire avec\t\n\tprint_memory\n\n\n\tlol.lol\n \0";
	unsigned char	all[40];
	for (int i = 0; i < 40; i++) all[i] = (unsigned char)(i * 7 + 200);
	C("ตัวอย่างจากโจทย์ (92 ไบต์)", s, sizeof(s));
	C("16 ไบต์พอดี 1 บรรทัด", s, 16);
	C("5 ไบต์ (บรรทัดไม่เต็ม ต้องเว้นช่องให้ตรง)", s, 5);
	C("ไบต์เกิน 127 + ตัวพิมพ์ไม่ได้", all, 40);
	{ char *got; cap_start(); ft_print_memory(s, 0); got = cap_end(); t_str("size = 0 ต้องไม่พิมพ์อะไร", got, ""); free(got); }
	return (t_done());
}
