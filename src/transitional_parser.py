from dataclasses import dataclass, field
from parse import parse

from .argument import Argument, EnumArgument
from .device import Device
from .parser import Parser, UTILITY


jump_fmt = '{addr}'
condition_fmt = '{cond} ? {left} : {right}'.replace(' ', '{:os}')


conditions = {
    value: idx for idx, value in enumerate(
        ['F', 'Z1', 'Z2', 'Z1 && Z2', 'X1', 'X2', 'X3', 'X4']
    )
}


def _addr(s: str):
    s = s.strip('A')
    
    return int(s)


@dataclass
class TransitionalParser(Parser):
    Addr1: Argument
    Addr2: Argument
    Flags: EnumArgument
    End: Argument

    _devices: list[Device] = field(default_factory=list, init=False)
    
    def parse_line(self, line: str):
        result = parse(condition_fmt, line, UTILITY)
        
        if result is None:
            result = parse(jump_fmt, line, UTILITY)
            
            assert result is not None, f"Unknown transition: {line}"
            
            if result['addr'] == 'END':
                return {
                    'End': '1'
                }
            
            return {
                'Addr1': f"{_addr(result['addr']):b}",
                'Addr2': f"{_addr(result['addr']):b}",
            }

        assert result is not None, f"Unknown transition: {line}"

        return {
            'Addr1': f"{_addr(result['left']):b}",
            'Addr2': f"{_addr(result['right']):b}",
            'Flags': result['cond']
        }

    def feed(self, idx: int, code: str):
        try:
            data = self.parse_line(code)
        except Exception as e:
            raise RuntimeError(f"Line {idx} error: {e}") from e
        
        # print(data)
        
        data = {
            key: value
            for mapping in [
                getattr(self, arg).create(data[arg], reverse=True)
                if arg in data else
                getattr(self, arg).create_default(reverse=True)
                for arg in [
                    'Addr1', 'Addr2', 'Flags', 'End'
                ] if getattr(self, arg)
            ]
            for key, value in mapping.items()
        }
        
        self.feed_devices(idx, **data)
