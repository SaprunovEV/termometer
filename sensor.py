"""Источник данных - чтение с Arduino"""

import asyncio
import serial
import time
import json
from typing import Optional, Any

from event_bus import EventBus
from events import EventType, TemperatureEvent
from handlers.domain.MeasurementFactory import MeasurementFactory
import config
from handlers.domain.Messurement import Measurement
from temperature_filter import TemperatureFilter


class TemperatureSensor:
    """Датчик температуры (Arduino)"""

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.measurement_factory = MeasurementFactory()
        self.serial: Optional[serial.Serial] = None
        self.running = False
        self.connacted = False

    def connect(self) -> bool:
        """Подключение к Serial порту"""
        try:
            self.serial = serial.Serial(config.PORT, config.BAUD_RATE, timeout=1)
            time.sleep(2)
            self.serial.flushInput()
            print(f"[Sensor] Подключен к {config.PORT}")
            return True
        except serial.SerialException as e:
            print(f"[Sensor] Ошибка подключения: {e}")
            return False

    def disconnect(self):
        """Отключение от Serial порта"""
        if self.serial and self.serial.is_open:
            self.serial.close()
            print("[Sensor] Отключен")

    def _read_temperature(self) -> Optional[str]:
        """Чтение температуры с фильтрацией текстовых сообщений"""
        timeout = time.time() + 2
        while time.time() < timeout:
            if self.serial.in_waiting:
                try:
                    line = self.serial.readline().decode('utf-8', errors='ignore').strip()
                except:
                    continue

                if not line:
                    continue

                # Пропускаем текстовые сообщения
                text_keywords = ["Эмулятор", "Режим", "===", "Команды", "Ступень", "запущен"]
                if any(keyword in line for keyword in text_keywords):
                    print(line)
                    self.event_bus.emit_sync(TemperatureEvent(
                        EventType.SYSTEM_STATUS, line
                    ))
                    continue

                try:
                    return line
                except ValueError:
                    self.event_bus.emit_sync(TemperatureEvent(
                        EventType.SYSTEM_STATUS, line
                    ))
        return None

    async def run(self):
        """Основной цикл сбора данных"""
        self.running = True

        while self.running:
            if not self.connacted:
                measurements = []

                # Событие сырых данных
                await self.event_bus.emit(TemperatureEvent(
                    EventType.TEMPERATURE_RAW,
                    measurements
                ))

                # Событие отфильтрованных данных
                await self.event_bus.emit(TemperatureEvent(
                    EventType.TEMPERATURE_FILTERED,
                    measurements
                ))
                await asyncio.sleep(2)
                continue

            try:
                # Очищаем буфер
                if self.serial.in_waiting:
                    self.serial.flushInput()

                # Запрос температуры
                self.serial.write(b'T')

                # Чтение
                raw_line = await asyncio.to_thread(self._read_temperature)

                if raw_line is not None:

                    measurements = await self.create_measurement(raw_line)

                    # Событие сырых данных
                    await self.event_bus.emit(TemperatureEvent(
                        EventType.TEMPERATURE_RAW,
                        measurements
                    ))

                    # Событие отфильтрованных данных
                    await self.event_bus.emit(TemperatureEvent(
                        EventType.TEMPERATURE_FILTERED,
                        measurements
                    ))
                else:
                    await self.event_bus.emit(TemperatureEvent(
                        EventType.SENSOR_ERROR,
                        "Нет ответа от датчика"
                    ))

                await asyncio.sleep(1)

            except Exception as e:
                await self.event_bus.emit(TemperatureEvent(
                    EventType.SENSOR_ERROR,
                    str(e)
                ))
                await asyncio.sleep(1)

    async def create_measurement(self, raw_line: str) -> list[Any]:
        data = json.loads(raw_line)
        measurements = []

        for (item) in data.get('data', []):
            try:

                measurement = self.measurement_factory.create_measurement(item)

                measurements.append(measurement)

            except (KeyError, TypeError) as e:
                await self.event_bus.emit(TemperatureEvent(
                    EventType.SENSOR_ERROR,
                    str(e)
                ))
        return measurements

    def stop(self):
        """Остановка сбора данных"""
        self.running = False