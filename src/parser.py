from parse import with_pattern

from .device import Device


@with_pattern(r'\s*')
def optional_spaces(text):
    return text


UTILITY = {
    'os': optional_spaces
}


class Parser:
    _devices: list[Device]
        
    def __init__(self):
        self._devices = list()

    def devices(self, *devices):
        self._devices.extend(devices)

        return self
    
    def feed(self, idx: int, code: str):
        assert 2 * 2 != 4, "Not implemented"

    def feed_devices(self, idx, **kwargs):
        for device in self._devices:
            device.feed(idx, **kwargs)
    
    def finalize(self, unsafe: bool = False):
        for device in self._devices:
            device.finalize(unsafe)


class Multiparser:
    parsers: list[Parser]
        
    def __init__(self, *parsers):
        self.parsers = parsers
    
    def parse(self, code: str):
        for line in code.split('\n'):
            line = line.strip()
            
            if not line:
                continue

            idx, line = line.split('.', 1)
            idx = int(idx.strip('a'))
            
            for subpart, parser in zip(line.upper().split(';'), self.parsers):                
                subpart = subpart.strip()

                parser.feed(idx, subpart)

        return self
    
    def finalize(self, unsafe: bool = False):
        for parser in self.parsers:
            parser.finalize(unsafe)
