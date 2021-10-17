from src.argument import Argument, EnumArgument
from src.device import Device, NestedDevice
from src.operational_parser import OperationalParser
from src.transitional_parser import TransitionalParser
from src.output_parser import OutputParser
from src.parser import Multiparser


FOLDER = 'T3'


ADDR1 = Argument('ADDR{}_1', 7)
ADDR2 = Argument('ADDR{}_2', 7)
A     = Argument('A{}', 4)
B     = Argument('B{}', 4)
D     = Argument('D{}', 4)
I     = Argument('I{}', 9)
C     = Argument('C{}', 1)
END   = Argument('END', 1).default('0')
CX    = EnumArgument('CX{}', 3).encoded('Z', 'C4', '1', '0', 'X1', 'X2', 'X3', 'X4').default('0')


u1 = Device(f'{FOLDER}/u7').bits(A, B)
u2 = Device(f'{FOLDER}/u5').bits(D, I[8], C, [0] * 2)
u3 = Device(f'{FOLDER}/u1').bits(I[:8])
u6 = Device(f'{FOLDER}/u22').bits(CX, END, [0] * 4)
u7 = Device(f'{FOLDER}/u18').bits(
    ADDR1[0], ADDR2[0], ADDR1[1], ADDR2[1], ADDR1[2], ADDR2[2], ADDR1[3], ADDR2[3]
)

parser1 = OperationalParser(A, B, D, C, I).devices(u1, u2, u3)
parser2 = TransitionalParser(ADDR1, ADDR2, CX, END).devices(u6, u7)

code = """
# y2
a0.  Y = 0100 || 0 ; a1             ;
a1.  NOP           ; x1 ? a13 : a2  ;
a2.  NOP           ; x2 ? a3 : a1   ;
# y2
a3.  Y = 0100 || 0 ; a4             ;
a4.  NOP           ; x1 ? a8 : a5   ;
a5.  NOP           ; x2 ? a0 : a6   ;
a6.  NOP           ; x3 ? a0 : a7   ;
a7.  NOP           ; x4 ? a3 : a4   ;
# y3
a8.  Y = 1000 || 0 ; a9             ;
a9.  NOP           ; x1 ? a8 : a10  ;
a10. NOP           ; x2 ? a3 : a11  ;
a11. NOP           ; x3 ? a13: a12  ;
a12. NOP           ; x4 ? a0 : a9   ;
# y1
a13. Y = 0010 || 0 ; a14            ;
a14. NOP           ; x1 ? a3 : a15  ;
a15. NOP           ; x2 ? a13 : a14 ;
"""

Multiparser(parser1, parser2).parse(code).finalize(unsafe=True)
