from handlers.domain.Messurement import Measurement
from temperature_filter import TemperatureFilter


class MeasurementFactory:
    """Фабрика для создания Measurement с правильным фильтром"""

    def __init__(self):
        self.filters = {}  # Хранилище фильтров по id

    def create_measurement(self, item) -> Measurement:
        """Создаёт или возвращает Measurement с фильтром"""
        sensor_id = item['id']

        if sensor_id in self.filters:
            _filter = self.filters[sensor_id]
        else:
            _filter = TemperatureFilter()
            self.filters[sensor_id] = _filter

        return Measurement(
            item['id'],
            item['value'],
            _filter=_filter
        )
