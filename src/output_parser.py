from .argument import EnumArgument
from .device import Device
from .parser import Parser, UTILITY

from parse import parse


output_fmt = "-> {line}".replace(' ', '{:os}')


class OutputParser(Parser):
    _arguments: list[EnumArgument]

    def __init__(self, *args):
        self._arguments = args

        super().__init__()
    
    def parse_line(self, line: str):
        if not line:
            return []

        result = parse(output_fmt, line, UTILITY)

        assert result is not None, f"Unknown output fmt: {line}"

        return [l.strip() for l in result['line'].split(',')]

    def feed(self, idx, line: str):
        try:
            data = self.parse_line(line)
        except Exception as e:
            raise RuntimeError(f"Line {idx} {type(self).__name__} error: {e}") from e
        
        result = dict()
        for arg in self._arguments:
            pieces = [piece for piece in data if piece in arg]

            assert len(pieces) < 2, f"Enum argument can only be in one position at a time: {pieces}"

            result.update(arg.create(pieces[0], reverse=True) if pieces else arg.create_default(reverse=True))

        self.feed_devices(idx, **result)
