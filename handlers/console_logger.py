"""Обработчик: вывод в консоль"""

from events import EventType, TemperatureEvent
import config


class ConsoleLogger:
    """Логирование в консоль"""

    def __init__(self, log_interval: int = None):
        self.log_interval = log_interval or config.CONSOLE_LOG_INTERVAL
        self.counter = 0

    async def handle_temperature(self, event: TemperatureEvent):
        """Обработка события температуры"""
        if event.type == EventType.TEMPERATURE_FILTERED:
            self.counter += 1
            data = event.data

            if self.counter % self.log_interval == 0 or abs(data.noise()) > 0.2:
                print(f"[{event.timestamp.strftime('%H:%M:%S')}] "
                      f"#{self.counter} | Raw: {data.value:.3f}°C → "
                      f"Filt: {data.filtered:.3f}°C "
                      f"(noise: {data.noise():+.3f}°C)")

    async def handle_status(self, event: TemperatureEvent):
        """Обработка статусных сообщений"""
        if event.type == EventType.SYSTEM_STATUS:
            print(f"[Arduino] {event.data}")

    async def handle_error(self, event: TemperatureEvent):
        """Обработка ошибок"""
        if event.type == EventType.SENSOR_ERROR:
            print(f"[Ошибка] {event.data}")