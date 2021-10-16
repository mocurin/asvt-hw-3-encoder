from src.argument import Argument, EnumArgument
from src.device import Device
from src.transitional_parser import TransitionalParser
from src.output_parser import OutputParser
from src.parser import Multiparser


FOLDER = 'T1'


ADDR1 = Argument('ADDR{}_1', 5)
ADDR2 = Argument('ADDR{}_2', 5)
END   = Argument('END', 1).default('1')
CX    = EnumArgument('CX{}', 2).encoded('X1', 'X2', 'X3', 'X4').default('X1')
DECR1 = EnumArgument('DECR{}_1', 3).encoded('0', 'y1', 'y2', 'y3', 'y11', 'y13', 'y14', 'yK').default('0')
DECR2 = EnumArgument('DECR{}_2', 2).encoded('0', 'y4', 'y6', 'y15').default('0')
DECR3 = EnumArgument('DECR{}_3', 2).encoded('0', 'y5', 'y8', 'y10').default('0')
DECR4 = EnumArgument('DECR{}_4', 2).encoded('0', 'y9', 'y16', 'y18').default('0')
DECR5 = EnumArgument('DECR{}_5', 2).encoded('0', 'y7', 'y12', 'y17').default('0')


u1 = Device(f'{FOLDER}/u4').bits(DECR1, DECR2, DECR3, 0)
u2 = Device(f'{FOLDER}/u5').bits(DECR4, DECR5, [0] * 4)
u3 = Device(f'{FOLDER}/u6').bits(ADDR1, CX, END)
u4 = Device(f'{FOLDER}/u7').bits(ADDR2, [0] * 3)


parser1 = TransitionalParser(ADDR1, ADDR2, CX, END).devices(u3, u4)
parser2 = OutputParser(DECR1, DECR2, DECR3, DECR4, DECR5).devices(u1, u2)


code = """
a0.  x1 ? a2 : a1;
a1.  x2 ? a5 : a4;
a2.  x2 ? a3 : a5;
a3.  a7;    -> y1, y5, y9;
a4.  a11;   -> y3, y4;
a5.  a6;    -> y2, y4;
a6.  a7;    -> y5, y9, y15;
a7.  x3 ? a10 : a8;
a8.  a9;    -> y7, y11;
a9.  a0;    -> yk;
a10. a11;   -> y6, y13;
a11. a12;   -> y7, y10;
a12. a13;   -> y5, y9, y11;
a13. x2 ? a15 : a14;
a14. x4 ? a17 : a18;
a15. x4 ? a18 : a16;
a16. a19;   -> y2, y15, y18;
a17. a21;   -> y12, y13;
a18. a19;   -> y10, y12, y14;
a19. x3 ? a20 : a11;
a20. a21;   -> y2, y6, y8, y17, 16;
a21. a9;    -> y10, y12, y15, y18;
"""


Multiparser(parser1, parser2).parse(code).finalize(unsafe=True)
