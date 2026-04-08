"""Главный файл запуска системы мониторинга температуры"""

import asyncio
import signal

from event_bus import EventBus
from events import EventType
from sensor import TemperatureSensor
from handlers import CSVWriter, ConsoleLogger, PlotUpdater, StatisticsCollector
import config


class TemperatureMonitor:
    """Главный класс приложения"""

    def __init__(self):
        self.event_bus = EventBus()
        self.sensor = TemperatureSensor(self.event_bus)

        # Создаём обработчики
        self.csv_writer = CSVWriter(config.CSV_FILE)
        self.console_logger = ConsoleLogger()
        self.plot_updater = PlotUpdater()
        self.statistics = StatisticsCollector()

        # Флаг завершения
        self.running = False

    def _setup_subscriptions(self):
        """Настройка подписок на события"""
        bus = self.event_bus

        # Подписываем обработчики
        bus.subscribe(EventType.TEMPERATURE_FILTERED, self.csv_writer.handle_temperature)
        bus.subscribe(EventType.TEMPERATURE_FILTERED, self.console_logger.handle_temperature)
        bus.subscribe(EventType.TEMPERATURE_FILTERED, self.plot_updater.handle_temperature)
        bus.subscribe(EventType.TEMPERATURE_FILTERED, self.statistics.handle_temperature)

        bus.subscribe(EventType.SYSTEM_STATUS, self.console_logger.handle_status)
        bus.subscribe(EventType.SENSOR_ERROR, self.console_logger.handle_error)

    async def run(self):
        """Запуск мониторинга"""
        print("\n" + "=" * 50)
        print("МОНИТОРИНГ ТЕМПЕРАТУРЫ (СОБЫТИЙНАЯ АРХИТЕКТУРА)")
        print("=" * 50 + "\n")

        # Подключаемся к датчику
        if not self.sensor.connect():
            print("[Ошибка] Не удалось подключиться к датчику")
            return

        # Настраиваем подписки
        self._setup_subscriptions()

        # Запускаем шину событий
        self.event_bus.start()
        self.running = True

        # Запускаем задачи
        tasks = [
            asyncio.create_task(self.sensor.run()),
            asyncio.create_task(self.event_bus.process_events())
        ]

        print("[Main] Система запущена. Нажмите Ctrl+C для остановки.\n")

        try:
            # Ждём завершения
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            pass
        except KeyboardInterrupt:
            print("\n[Main] Получен сигнал остановки...")
        finally:
            await self.shutdown(tasks)

    async def shutdown(self, tasks: list):
        """Корректное завершение работы"""
        print("[Main] Завершение работы...")

        self.running = False
        self.sensor.stop()
        self.event_bus.stop()

        # Отменяем задачи
        for task in tasks:
            task.cancel()

        # Ждём завершения
        await asyncio.gather(*tasks, return_exceptions=True)

        # Закрываем ресурсы
        self.sensor.disconnect()
        self.csv_writer.close()
        self.statistics.print_summary()

        print("[Main] Система остановлена.")
        print("\nЗакройте окно графика для выхода...")

        # Показываем финальный график
        self.plot_updater.show_blocking()


def main():
    """Точка входа"""
    monitor = TemperatureMonitor()

    # Настройка обработки сигналов
    def signal_handler(sig, frame):
        print("\n[Main] Прерывание...")

    signal.signal(signal.SIGINT, signal_handler)

    try:
        asyncio.run(monitor.run())
    except KeyboardInterrupt:
        print("\n[Main] Программа остановлена.")


if __name__ == "__main__":
    main()