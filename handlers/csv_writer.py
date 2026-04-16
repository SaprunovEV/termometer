"""Обработчик: запись в CSV файл"""

import csv
import os
from datetime import datetime

from events import EventType, TemperatureEvent


class CSVWriter:
    """Запись данных в CSV файл"""

    def __init__(self, filename: str):
        self.filename = filename
        self.file = None
        self.writer = None
        self.measurement_count = 0
        self._open_file()

    def _open_file(self):
        """Открыть файл для записи"""
        os.makedirs("./data", exist_ok=True)

        # Заменяем двоеточия на дефисы или точки
        now = datetime.now()
        safe_time = now.isoformat().replace(':', '-')  # или replace(':', '.')

        self.file = open(f"./data/{safe_time}{self.filename}", 'w', newline='', encoding='utf-8')
        self.writer = csv.writer(self.file)
        self.writer.writerow(['Termometr ID','Timestamp', 'Raw_Temp', 'Filtered_Temp', 'Noise'])

    async def handle_temperature(self, event: TemperatureEvent):
        """Обработка события температуры"""
        if event.type == EventType.TEMPERATURE_FILTERED:
            data = event.data
            for item in data:
                self.writer.writerow([
                    f"{item.ter_id}",
                    event.timestamp.isoformat(),
                    f"{item.value:.3f}",
                    f"{item.filtered:.3f}",
                    f"{item.noise():.3f}"
                ])
            self.file.flush()
            self.measurement_count += 1

    def close(self):
        """Закрыть файл"""
        if self.file:
            self.file.close()
            print(f"[CSVWriter] Записано {self.measurement_count} измерений в {self.filename}")