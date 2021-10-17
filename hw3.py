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
u4 = Device(f'{FOLDER}/u9').bits(I1[:4], I2[:4])
u5 = Device(f'{FOLDER}/u11').bits(I1[4:8], I2[4:8])
u6 = Device(f'{FOLDER}/u22').bits(CX, END, [0] * 4)
u7 = Device(f'{FOLDER}/u13').bits(I1[8], I2[8], C1, C2, [0] * 4)
u8 = Device(f'{FOLDER}/u18').bits(ADDR1, 0)
u9 = Device(f'{FOLDER}/u20').bits(ADDR2, 0)
u5_a = NestedDevice(u5).bits(DECR1, DECR2, DECR3, 0)
u7_a = NestedDevice(u7).bits(DECR4, DECR5, [0] * 4)


parser1 = OperationalParser(A1, B1, D1, C1, I1).devices(u1, u2, u3, u4, u5, u6, u7)
parser2 = OperationalParser(A2, B2, D2, C2, I2).devices(u1, u2, u3, u4, u5, u6, u7)
parser3 = TransitionalParser(ADDR1, ADDR2, CX, END).devices(u6, u8, u9)
parser4 = OutputParser(DECR1, DECR2, DECR3, DECR4, DECR5).devices(u5_a, u7_a)

code = """
# Команда загрузки. Пока флаг загрузки поднят - повторяем команду
# X, XXXX - синтаксичечкий сахар для 0 и 0000 - мы просто не вбиваем
# здесь данные поскольку их ввод будет перехвачен пока поднят флаг L
a0.  POH[X] = XXXX || 0                               ; POH[X] = XXXX || 0                               ; L ? a0 : a1          ;

# 15 регистр - младшие биты чисел
a1.  Y = 0 || POH[15]                                 ; Y = 0 || POH[15]                                 ; z1 && z2 ? a23 : a2  ;

# Создаем маску 0001 в PQ каждого КМ
a2.  Q = 0 + Q + 1                                    ; Q = 0 + Q + 1                                    ; a3                   ;

# Шаг алгоритма:
# 1. Накладываем маску на POH[15] 1KM, не трогаем второй -
# поскольку можем проверять только 1 флаг за раз
a3.  Y = POH[15] && Q                                 ; NOP                                              ; z1 ? a5 : a4         ;

# Z1 == 0 -> бит единичный, устанавливаем число A из D в РОН[0]
a4.  POH[0] = XXXX || 0                               ; NOP                                              ; a5                   ;

# Z1 == 1 -> бит нулевой, пропуск. Аналогично для 2КМ
a5.  NOP                                              ; Y = POH[15] && Q                                 ; z2 ? a7 : a6         ;
a6.  NOP                                              ; POH[0] = XXXX || 0                               ; a7                   ;

# После проверки двух КМ сдвигаем маску на 1 влево: 0010. Учитываем то, что двигается содержимое 13 регистра - его лучше не использовать
a7.  F = 0 && POH[13], F << 1 -> POH[13], Q << 1 -> Q ; F = 0 && POH[13], F << 1 -> POH[13], Q << 1 -> Q ; a8                   ;
a8.  Y = POH[15] && Q                                 ; NOP                                              ; z1 ? a10 : a9        ;

# Делаем аналогично для POH[1] и т.д.
a9.  POH[1] = XXXX || 0                               ; NOP                                              ; a10                  ;
a10. NOP                                              ; Y = POH[15] && Q                                 ; z2 ? a12 : a11       ;
a11. NOP                                              ; POH[1] = XXXX || 0                               ; a12                  ;

# Маска 0100
a12. F = 0 && POH[13], F << 1 -> POH[13], Q << 1 -> Q ; F = 0 && POH[13], F << 1 -> POH[13], Q << 1 -> Q ; a13                  ;
a13. Y = POH[15] && Q                                 ; NOP                                              ; z1 ? a15 : a14       ;
a14. POH[2] = XXXX || 0                               ; NOP                                              ; a15                  ;
a15. NOP                                              ; Y = POH[15] && Q                                 ; z2 ? a17 : a16       ;
a16. NOP                                              ; POH[2] = XXXX || 0                               ; a17                  ;

# Маска 1000
a17. F = 0 && POH[13], F << 1 -> POH[13], Q << 1 -> Q ; F = 0 && POH[13], F << 1 -> POH[13], Q << 1 -> Q ; a18                  ;
a18. Y = POH[15] && Q                                 ; NOP                                              ; z1 ? a20 : a19       ;
a19. POH[3] = XXXX || 0                               ; NOP                                              ; a20                  ;
a20. NOP                                              ; Y = POH[15] && Q                                 ; z2 ? a22 : a21       ;
a21. NOP                                              ; POH[3] = XXXX || 0                               ; a22                  ;

# В D не гарантировано наличие 0000 - обнуляем Q 
a22. Q = 0 && Q                                       ; Q = 0 && Q                                       ; a23                  ;

# 14 регистр - старшие биты чисел
a23. Y = 0 || POH[14]                                 ; Y = 0 || POH[14]                                 ; z1 && z2 ? a44 : a24 ;

# Без этой и предыдущей команды можно было обойтись, сдвигая маску в обратном
# направлении но если первая часть была пропущена, то тогда маска будет
# в состоянии 0000 и из нее нужно будет сделать 1000, это менее очевидно
# и требует столько же команд
a24. Q = 0 + Q + 1                                    ; Q = 0 + Q + 1                                    ; a25                  ;
a25. Y = POH[14] && Q                                 ; NOP                                              ; z1 ? a27 : a26       ;
a26. POH[4] = XXXX || 0                               ; NOP                                              ; a27                  ;
a27. NOP                                              ; Y = POH[14] && Q                                 ; z2 ? a29 : a28       ;
a28. NOP                                              ; POH[4] = XXXX || 0                               ; a29                  ;
a29. F = 0 && POH[13], F << 1 -> POH[13], Q << 1 -> Q ; F = 0 && POH[13], F << 1 -> POH[13], Q << 1 -> Q ; a30                  ;
a30. Y = POH[14] && Q                                 ; NOP                                              ; z1 ? a32 : a31       ;
a31. POH[5] = XXXX || 0                               ; NOP                                              ; a32                  ;
a32. NOP                                              ; Y = POH[14] && Q                                 ; z2 ? a34 : a33       ;
a33. NOP                                              ; POH[5] = XXXX || 0                               ; a34                  ;
a34. F = 0 && POH[13], F << 1 -> POH[13], Q << 1 -> Q ; F = 0 && POH[13], F << 1 -> POH[13], Q << 1 -> Q ; a35                  ;
a35. Y = POH[14] && Q                                 ; NOP                                              ; z1 ? a37 : a36       ;
a36. POH[6] = XXXX || 0                               ; NOP                                              ; a37                  ;
a37. NOP                                              ; Y = POH[14] && Q                                 ; z2 ? a39 : a38       ;
a38. NOP                                              ; POH[6] = XXXX || 0                               ; a39                  ;
a39. F = 0 && POH[13], F << 1 -> POH[13], Q << 1 -> Q ; F = 0 && POH[13], F << 1 -> POH[13], Q << 1 -> Q ; a40                  ;
a40. Y = POH[14] && Q                                 ; NOP                                              ; z1 ? a42 : a41       ;
a41. POH[7] = XXXX || 0                               ; NOP                                              ; a42                  ;
a42. NOP                                              ; Y = POH[14] && Q                                 ; z2 ? a44 : a43       ;
a43. NOP                                              ; POH[7] = XXXX || 0                               ; a44                  ;

# Завершаем работу алгоритма
a44. NOP                                              ; NOP                                              ; END                  ;

# Задание №2
a64. ; ; x1 ? a66 : a65 ;
a65. ; ; x2 ? a69 : a68 ;
a66. ; ; x2 ? a67 : a69 ;
a67. ; ; a71            ; -> y1, y5, y9
a68. ; ; a75            ; -> y3, y4
a69. ; ; a70            ; -> y2, y4
a70. ; ; a71            ; -> y5, y9, y15
a71. ; ; x3 ? a74 : a72 ;
a72. ; ; a73            ; -> y7, y11
a73. ; ; a64            ; -> yk
a74. ; ; a75            ; -> y6, y13
a75. ; ; a76            ; -> y7, y10
a76. ; ; a77            ; -> y5, y9, y11
a77. ; ; x2 ? a79 : a78 ;
a78. ; ; x4 ? a81 : a82 ;
a79. ; ; x4 ? a82 : a80 ;
a80. ; ; a83            ; -> y2, y15, y18
a81. ; ; a85            ; -> y12, y13
a82. ; ; a83            ; -> y10, y12, y14
a83. ; ; x3 ? a84 : a75 ;
a84. ; ; a85            ; -> y2, y6, y8, y17, 16
a85. ; ; a73            ; -> y10, y12, y15, y18
"""

Multiparser(parser1, parser2, parser3, parser4).parse(code).finalize(unsafe=True)
