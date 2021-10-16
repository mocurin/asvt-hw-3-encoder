from enum import Enum

class IHEXFieldType(Enum):
    BIN_DATA = '00'
    FILE_END = '01'
    SEG_ADDR = '02'


def complement(value, bits) -> int:
    return value ^ ((2 ** bits) - 1)


def lookback(gen, back=1) -> tuple:
    gen = iter(gen)
    
    back = [next(gen) for _ in range(back)]
    
    for value in gen:
        yield (*back, value)
        
        back = [*back[1:], value]
        
    yield (*back, None)


class IHEX80:
    @classmethod
    def checksum(cls, line):
        # Чексумма строки
        bts = (int(a + b, 16) for a, b in zip(line[::2], line[1::2]))
        return f"{complement(sum(bts), len(line) // 2) + 1:x}"[-2:]
    
    @classmethod
    def line(cls, A: str, D: str, chunksize: int = None, T: IHEXFieldType = IHEXFieldType.BIN_DATA):
        if chunksize:
            D = f"{D:0<{chunksize * 2}}"
        
        # Строка с данными
        line = f"{len(D) // 2:02x}{A}{T.value}{D}"

        return f":{line}{cls.checksum(line)}".upper()
    
    @classmethod
    def endl(cls):
        # Завершающая строка файла
        return cls.line('0000', '', None, IHEXFieldType.FILE_END)

    @classmethod
    def encode(cls, data: dict[str, str], chunksize: int = 16):
        # Границы адресного пространства
        min_addr, max_addr = min(data), max(data)

        # Непрерывное пространство
        memory = ['00' for _ in range(max_addr - min_addr + 1)]
        for key, value in data.items():
            memory[key - min_addr] = value

        # Строки файла
        return [
            *[
                cls.line(
                    f"{idx + min_addr:04x}",
                    ''.join(memory[idx:jdx]),
                    chunksize, IHEXFieldType.BIN_DATA,
                ) + '\n'
                for (idx, jdx) in lookback(range(0, len(data), chunksize))
                if not all(sym == '0' for sym in memory[idx:jdx])
            ],
            cls.endl()
        ]
    
    @classmethod
    def save(cls, filename: str = 'firmware.hex', *args, **kwargs):
        with open(filename, 'w+') as file:
            file.writelines(
                cls.encode(*args, **kwargs)
            )