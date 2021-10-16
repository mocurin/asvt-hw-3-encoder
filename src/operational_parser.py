from dataclasses import dataclass, field
from parse import parse

from .argument import Argument
from .device import Device
from .parser import Parser, UTILITY


store_fmt   = '{src} -> {dest}'.replace(' ', '{:os}')
command_fmt = '{result} = {cmd}'.replace(' ', '{:os}')


MF2 = 'F << 1'
MQ2 = 'Q << 1'
DF2 = 'F >> 1'
DQ2 = 'Q >> 1'

Y = 'Y'
F = 'F'

A = 'A'
B = 'B'
D = 'D'
O = '0'
Q = 'Q'


load = {
    value: idx for idx, value in enumerate(
        [
            (A, Q), (A, B),
            (O, Q), (O, B),
            (O, A), (D, A),
            (D, Q), (D, O)
        ]
    )
}

commands = {
    value.replace(' ', '{:os}'): idx for idx, value in enumerate(
        [
            '{left} + {right} + {const}',
            '{right} - {left} - 1 + {const}',
            '{left} - {right} - 1 + {const}',
            '{left} || {right}',
            '{left} && {right}',
            '!{left} && {right}',
            '{left} ^ {right}',
            '!({left} ^ {right})'
        ]
    )
}

store = {
    value: idx for idx, value in enumerate(
        [
            (F, Q), (F, Y), (F, B), (F, B),
            ((DF2, B), (DQ2, Q)), (DF2, B),
            ((MF2, B), (MQ2, Q)), (MF2, B)
        ]
    )
}

input_arguments = {
    Q: Q, O: O, '{data}': D, 'POH[{addr}]': (A, B),
}

storing_arguments = {
    Q: Q, Y: Y, MF2: MF2, MQ2: MQ2, DF2: DF2, DQ2: DQ2, 'POH[{addr}]': B
}


def parse_argument(line: str, arguments: dict):
    for fmt, var in arguments.items():
        data = None
        if fmt == line:
            return data, var

        elif result := parse(fmt, line):
            if B in var:
                data = result['addr']

                # Костыль для загрузки - указываем X когда адрес все равно подменят
                if data == 'X':
                    return '0000', var
                
                data = int(data)
                
                assert data >= 0 and data < 16, f"POH address arguments are positive integers in range [0, 16): `{data}`"
                
                data = f"{data:04b}"

                return data, var
            elif var == D:
                data = result['data']

                # Костыль для загрузки - указываем XXXX когда данные все равно подменят
                if data == 'XXXX':
                    return '0000', var
                
                assert isinstance(data, str) and len(data) == 4 and not (set(data) - {'0', '1'}), f"Data arguments should be binary strings of length 2: `{data}`"

                return data, var

    raise RuntimeError(f"Unknown argument fmt: `{line}`")


def parse_storing_argument(line: str):
    try:
        return parse_argument(line, storing_arguments)
    except RuntimeError as e:
        raise RuntimeError(f"Storing argument error: {e}") from e


def parse_storing(line: str):
    result = parse(store_fmt, line, UTILITY)
    
    assert result is not None, f"Unknown storing fmt: {line}"
    
    nop, src = parse_storing_argument(result['src'])
    data, dest = parse_storing_argument(result['dest'])
    
    assert nop is None, f"First storing argument should be trivial: Q, F, F/2, 2F, received: {src}:{nop}"
    
    return data, (src, dest)


def parse_command_argument(line: str):
    try:
        return parse_argument(line, input_arguments)
    except RuntimeError as e:
        raise RuntimeError(f"Command argument error: {e}") from e


def parse_command(line: str):
    for fmt, idx in commands.items():
        if result := parse(fmt, line, UTILITY):        
            return idx, result.named
    raise RuntimeError(f"Unknown command fmr: {line}")


def parse_line(line: str):
    command, *storings = [l.strip() for l in line.split(',')]

    # Named result notation: F/Q/B = cmd_result
    result_a = parse(command_fmt, command, UTILITY)
    # Inplace result notation: cmd_result -> F/Q/B
    result_b = parse(store_fmt, command, UTILITY)
    
    assert result_a or result_b, f"Unkwown storing fmt: {command}"

    if result_a:
        command = result_a['cmd']
        dest = result_a['result']
        data, dest = parse_storing_argument(dest)

    elif result_b:
        command = result_b['src']
        dest = result_b['dest']
        data, dest = parse_storing_argument(dest)
    
    assert not (dest != F and storings), f"Shifts are only available when storing cmd result to F: {command}"
    
    if dest == F and storings:
        storings = list()

        for storing in storings:
            data, storing = parse_storing(storing)
            
            storings.append(storing)
        
        storings = tuple(storings)
    else:
        storings = (F, Y if dest == F else dest)
    
    storing_idx = store.get(storings)
    
    assert storing_idx is not None, f"Unknown storing arguments: {storings}"
        
    storing = tuple(
        parse_storing(storing) for storing in storings
    ) if dest == F and storings else (
        F, Y if dest == F else dest
    )
    
    command_idx, args = parse_command(command)
    
    left, var_l = parse_command_argument(args['left'])
    
    if A in var_l:
        var_l = A
    
    right, var_r = parse_command_argument(args['right'])
    
    if B in var_r:
        var_b = B
    
    # Load A B with B present in storing
    if var_l == A and var_r == B and data == left:
        left, right = right, left
        var_l, var_r = var_r, var_l

        command_idx += 1
    
    if var_r == B and data:
        assert data == right, f"B address missmatch: cmd B: {right} vs str B: {data}"     
        
    load_idx = load.get((var_l, var_r))
    
    assert load_idx is not None, f"Unknown load arguments: {(var_l, var_r)}"
    
    data = {
        var_l: left,
        var_r: right,
        'I': f"{storing_idx:03b}{command_idx:03b}{load_idx:03b}"
    }
    if command_idx in {1, 2}:
        assert args['const'] in {'0', '1'}
        data['C'] = f"{args['const']:b}"

    return data


@dataclass
class OperationalParser(Parser):
    A: Argument
    B: Argument
    D: Argument
    C: Argument
    I: Argument

    _devices: list[Device] = field(default_factory=list, init=False)
        
    def feed(self, idx: int, code: str) -> None:
        try:
            data = parse_line(code)
        except Exception as e:
            raise RuntimeError(f"Line {idx} {type(self).__name__} error: {e}") from e

        print(data)
        
        data = {
            key: value
            for mapping in [
                getattr(self, arg).create(data[arg], reverse=True)
                if arg in data else
                getattr(self, arg).create_default(reverse=True)
                for arg in [
                    'A', 'B', 'C', 'D', 'I'
                ] if getattr(self, arg)
            ]
            for key, value in mapping.items()
        }
    
        self.feed_devices(idx, **data)
