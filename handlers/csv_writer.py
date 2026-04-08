"""Обработчик: запись в CSV файл"""

import csv

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
        self.file = open(self.filename, 'w', newline='', encoding='utf-8')
        self.writer = csv.writer(self.file)
        self.writer.writerow(['Timestamp', 'Raw_Temp', 'Filtered_Temp', 'Noise'])

    async def handle_temperature(self, event: TemperatureEvent):
        """Обработка события температуры"""
        if event.type == EventType.TEMPERATURE_FILTERED:
            data = event.data
            self.writer.writerow([
                event.timestamp.isoformat(),
                f"{data['raw']:.3f}",
                f"{data['filtered']:.3f}",
                f"{data['noise']:.3f}"
            ])
            self.file.flush()
            self.measurement_count += 1

    def close(self):
        """Закрыть файл"""
        if self.file:
            self.file.close()
            print(f"[CSVWriter] Записано {self.measurement_count} измерений в {self.filename}")