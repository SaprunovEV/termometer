"""Главный файл запуска системы мониторинга температуры"""

import asyncio
import signal
import threading

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
        self.statistics = StatisticsCollector()

        # PlotUpdater создаём позже, так как ему нужен callback на self
        self.plot_updater = None

        # Флаги завершения
        self.running = False
        self._shutdown_event = asyncio.Event()

        # Мониторинг окна
        self._window_monitor_task = None

    def _setup_subscriptions(self):
        """Настройка подписок на события"""
        bus = self.event_bus

        # Подписываем обработчики
        bus.subscribe(EventType.TEMPERATURE_FILTERED, self.csv_writer.handle_temperature)
        bus.subscribe(EventType.TEMPERATURE_FILTERED, self.console_logger.handle_temperature)
        bus.subscribe(EventType.TEMPERATURE_FILTERED, self.statistics.handle_temperature)

        if self.plot_updater:
            bus.subscribe(EventType.TEMPERATURE_FILTERED, self.plot_updater.handle_temperature)

        bus.subscribe(EventType.SYSTEM_STATUS, self.console_logger.handle_status)
        bus.subscribe(EventType.SENSOR_ERROR, self.console_logger.handle_error)

    def request_shutdown(self):
        """Запросить завершение программы (вызывается из любого потока)"""
        if not self._shutdown_event.is_set():
            print("\n[Main] Запрошено завершение программы...")
            self._shutdown_event.set()

    async def _monitor_window(self):
        """Мониторинг состояния окна графика"""
        while self.running:
            await asyncio.sleep(0.5)  # Проверяем каждые 500 мс

            if self.plot_updater and not self.plot_updater.is_window_alive():
                print("\n[Main] Обнаружено закрытие окна графика.")
                self.request_shutdown()
                break

    async def run(self):
        """Запуск мониторинга"""
        print("\n" + "=" * 60)
        print("    МОНИТОРИНГ ТЕМПЕРАТУРЫ (СОБЫТИЙНАЯ АРХИТЕКТУРА)")
        print("=" * 60 + "\n")

        # Подключаемся к датчику
        if not self.sensor.connect():
            print("[Ошибка] Не удалось подключиться к датчику")
            return

        # Создаём PlotUpdater с callback'ом на завершение
        self.plot_updater = PlotUpdater(on_exit_callback=self.request_shutdown)

        # Настраиваем подписки
        self._setup_subscriptions()

        # Запускаем шину событий
        self.event_bus.start()
        self.running = True

        # Запускаем задачи
        sensor_task = asyncio.create_task(self.sensor.run())
        events_task = asyncio.create_task(self.event_bus.process_events())
        self._window_monitor_task = asyncio.create_task(self._monitor_window())

        print("[Main] Система запущена.")
        print("[Main] Способы завершения:")
        print("        🔴 Кнопка 'ЗАВЕРШИТЬ' на графике")
        print("        ❌ Крестик закрытия окна")
        print("        ⌨️  Ctrl+C в консоли")
        print()

        # Создаём задачу для ожидания сигнала завершения
        shutdown_task = asyncio.create_task(self._shutdown_event.wait())

        all_tasks = [sensor_task, events_task, self._window_monitor_task, shutdown_task]

        try:
            # Ждём первое событие завершения
            done, pending = await asyncio.wait(
                all_tasks,
                return_when=asyncio.FIRST_COMPLETED
            )

            # Определяем причину завершения
            if shutdown_task in done:
                print("[Main] Получен сигнал завершения.")
            elif self._window_monitor_task in done:
                print("[Main] Окно графика было закрыто.")
            elif sensor_task in done:
                try:
                    sensor_task.result()
                except Exception as e:
                    print(f"[Main] Сенсор завершился с ошибкой: {e}")

        except asyncio.CancelledError:
            pass
        except KeyboardInterrupt:
            print("\n[Main] Получен сигнал Ctrl+C...")
        finally:
            await self.shutdown(all_tasks)

    async def shutdown(self, tasks: list):
        """Корректное завершение работы"""
        print("[Main] Завершение работы...")

        self.running = False
        self.sensor.stop()
        self.event_bus.stop()

        # Устанавливаем событие завершения (на случай если ещё не установлено)
        self._shutdown_event.set()

        # Отменяем все задачи
        for task in tasks:
            if task and not task.done():
                task.cancel()

        # Ждём завершения с таймаутом
        await asyncio.gather(*[t for t in tasks if t], return_exceptions=True)

        # Закрываем ресурсы
        self.sensor.disconnect()
        self.csv_writer.close()
        self.statistics.print_summary()

        # Закрываем график (если ещё открыт)
        if self.plot_updater:
            if self.plot_updater.is_window_alive():
                self.plot_updater.close()

        print("\n[Main] Система остановлена.")
        print("[Main] Программа завершена.")


def main():
    """Точка входа"""
    monitor = TemperatureMonitor()

    try:
        asyncio.run(monitor.run())
    except KeyboardInterrupt:
        print("\n[Main] Программа остановлена.")


if __name__ == "__main__":
    main()