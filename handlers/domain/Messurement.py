
from temperature_filter import TemperatureFilter


class Measurement:
    ter_id: str
    value: float
    _filter: TemperatureFilter
    filtered: float = None

    def __init__(self, ter_id: str, value: float, _filter: TemperatureFilter):
        self.ter_id = ter_id
        self.value = value
        self._filter = _filter
        self.filtered = self._filter.filter(self.value)

    def noise(self):
        return self.value - self.filtered