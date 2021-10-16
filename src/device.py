from .argument import Argument
from .ihex80 import IHEX80


class LabeledDevice:
    _labels: list[str]

    def __init__(self):
        self._labels = list()

    def bits(self, *bits):
        self._labels = [
            str(label)
            for labels in [
                value if isinstance(value, list) or isinstance(value, Argument) else [value]
                for value in bits
            ]
            for label in labels
        ]

        return self

class Device(LabeledDevice):
    _name: str
    _data: dict[int, str]
    
    def __init__(self, name: str):
        self._name = name
        self._data = dict()
        
        super().__init__()
    
    def __getitem__(self, item):
        return self._data.get(item, [None for _ in self._labels])

    def feed(self, idx, **kwargs):
        self._data[idx] = [
            kwargs.get(label, None) if prev is None else prev
            for label, prev in zip(self._labels, self[idx])
        ]
    
    def finalize(self, unsafe: bool = False):
        for idx, bits in self._data.items():
            if unsafe:
                self._data[idx] = ['0' if bit is None else bit for bit in bits]
            else:
                assert not any(bit is None for bit in bits), f"Undefined bit on {idx}: {bits}"

        IHEX80.save(
            f"{self._name}.hex", {
                idx: f"{int(''.join(bits[::-1]), 2):02x}"
                for idx, bits in self._data.items()
            }
        )


class NestedDevice(LabeledDevice):
    _host: Device

    def __init__(self, device: Device):
        self._host = device
        
        super().__init__()
    
    def __getitem__(self, item):
        return self._host[item]

    def feed(self, idx, **kwargs):
        self._host._data[idx] = [
            kwargs.get(label, None) if prev is None else prev
            for label, prev in zip(self._labels, self[idx])
        ]
    
    def finalize(self, *args, **kwargs):
        return
