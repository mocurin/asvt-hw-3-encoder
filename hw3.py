from src.argument import Argument, EnumArgument
from src.device import Device, NestedDevice
from src.operational_parser import OperationalParser
from src.transitional_parser import TransitionalParser
from src.output_parser import OutputParser
from src.parser import Multiparser


FOLDER = 'HW3'


ADDR1 = Argument('ADDR{}_1', 7)
ADDR2 = Argument('ADDR{}_2', 7)
A1    = Argument('A{}_1', 4)
A2    = Argument('A{}_2', 4)
B1    = Argument('B{}_1', 4)
B2    = Argument('B{}_2', 4)
D1    = Argument('D{}_1', 4)
D2    = Argument('D{}_2', 4)
I1    = Argument('I{}_1', 9)
I2    = Argument('I{}_2', 9)
C1    = Argument('C{}_1', 1)
C2    = Argument('C{}_2', 1)
END   = Argument('END', 1).default('0')
CX    = EnumArgument('CX{}', 3).encoded('L', 'Z1', 'Z2', 'Z1 && Z2', 'X1', 'X2', 'X3', 'X4').default('L')
DECR1 = EnumArgument('DECR{}_1', 3).encoded('0', 'y1', 'y2', 'y3', 'y11', 'y13', 'y14', 'yK').default('0')
DECR2 = EnumArgument('DECR{}_2', 2).encoded('0', 'y4', 'y6', 'y15').default('0')
DECR3 = EnumArgument('DECR{}_3', 2).encoded('0', 'y5', 'y8', 'y10').default('0')
DECR4 = EnumArgument('DECR{}_4', 2).encoded('0', 'y9', 'y16', 'y18').default('0')
DECR5 = EnumArgument('DECR{}_5', 2).encoded('0', 'y7', 'y12', 'y17').default('0')


u1 = Device(f'{FOLDER}/u1').bits(A1, A2)
u2 = Device(f'{FOLDER}/u5').bits(B1, B2)
u3 = Device(f'{FOLDER}/u7').bits(D1, D2)
u4 = Device(f'{FOLDER}/u9').bits(I1[:8])
u5 = Device(f'{FOLDER}/u11').bits(I2[:8])
u6 = Device(f'{FOLDER}/u22').bits(CX, END, [0] * 4)
u7 = Device(f'{FOLDER}/u13').bits(I1[8], I2[8], C1, C2, [0] * 4)
u8 = Device(f'{FOLDER}/u18').bits(ADDR1, 0)
u9 = Device(f'{FOLDER}/u20').bits(ADDR2, 0)
u5_a = NestedDevice(u5).bits(DECR1, DECR2, DECR3, 0)
u7_a = NestedDevice(u7).bits(DECR4, DECR5, [0] * 4)


parser1 = OperationalParser(A1, B1, D1, C1, I1).devices(u1, u2, u3, u4, u6, u7, u9)
parser2 = OperationalParser(A2, B2, D2, C2, I2).devices(u1, u2, u3, u5, u6, u7, u9)
parser3 = TransitionalParser(ADDR1, ADDR2, CX, END).devices(u6, u8, u9)
parser4 = OutputParser(DECR1, DECR2, DECR3, DECR4, DECR5).devices(u5_a, u7_a)

code = """
# Команда загрузки. Пока флаг загрузки поднят - повторяем команду
# X, XXXX - синтаксичечкий сахар для 0 и 0000 - мы просто не вбиваем
# здесь данные поскольку их ввод будет перехвачен пока поднят флаг L
a0. POH[X] = XXXX || 0; POH[X] = XXXX || 0; L ? a0 : a1;

# Завершаем выполнение
a1. NOP               ; NOP               ; END        ;
"""

Multiparser(parser1, parser2, parser3, parser4).parse(code).finalize(unsafe=True)
