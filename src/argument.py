from typing import Any


class Argument:
    _labels: list[str]
    _default: list[str]
    
    def __init__(self, flabel: str, size: int):
        self._labels = [flabel.format(idx) for idx in range(size)]

        self._default = list()

    def __getitem__(self, item):
        return self._labels[item]
    
    def __iter__(self):
        return iter(self._labels)
        
    def __repr__(self):
        return str(self._labels)

    def default(self, *args, reverse: bool = False) -> 'Argument':
        if len(args) == 1:
            argument, *_ = args

            assert argument in {'0', '1', None}

            self._default = [
                None if argument is None else str(argument)
            ]
        
        else:
            assert len(args) == len(self._labels), f"Arguments default value shape mismatch: {args}"

            assert not set(args).difference({'0', '1', None}), f"Unacceptable values in default vector: {args}"

            self._default = list(args[::-1]) if reverse else args

        return self
    
    def create(self, data: str, reverse=False):
        data = f"{data:0>{len(self._labels)}}"
        
        return {label: bit for label, bit in zip(self._labels, data[::-1] if reverse else data)}


    def create_default(self, reverse=False):
        return self.create(''.join(self._default), reverse)


class EnumArgument(Argument):
    _default: str
    _possible: dict[str, int]

    def __init__(self, *args, **kwargs):
        self._possible = list()

        super().__init__(*args, **kwargs)
    
    def default(self, *args) -> 'EnumArgument':
        assert len(args) == 1, f"EnumArgument takes single default argument: {args}"

        self._default = args[0]

        return self

    def encoded(self, *args) -> 'EnumArgument':
        self._possible = {
            value.upper(): idx for idx, value in enumerate(args)
        }

        return self
    
    def create(self, data: str, reverse: bool = False):
        data = self._possible[data]

        data = f"{data:0>{len(self._labels)}b}"

        return {label: bit for label, bit in zip(self._labels, data[::-1] if reverse else data)}
    
    def create_default(self, reverse: bool = False):
        return self.create(self._default, reverse)
    
    def __contains__(self, value):
        return value in self._possible
        