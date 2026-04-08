"""Обработчик: сбор статистики"""

import numpy as np

from events import EventType, TemperatureEvent


class StatisticsCollector:
    """Сбор статистики по измерениям"""

    def __init__(self):
        self.raw_values = []
        self.filtered_values = []
        self.noise_values = []

    async def handle_temperature(self, event: TemperatureEvent):
        """Обработка события температуры"""
        if event.type == EventType.TEMPERATURE_FILTERED:
            data = event.data
            self.raw_values.append(data['raw'])
            self.filtered_values.append(data['filtered'])
            self.noise_values.append(data['noise'])

    def print_summary(self):
        """Вывод сводной статистики"""
        if not self.noise_values:
            print("[Stats] Нет данных для статистики")
            return

        noise_arr = np.array(self.noise_values)
        raw_arr = np.array(self.raw_values)

        print("\n" + "=" * 50)
        print("СТАТИСТИКА ИЗМЕРЕНИЙ")
        print("=" * 50)
        print(f"Количество измерений: {len(noise_arr)}")
        print(f"Средняя температура: {np.mean(raw_arr):.3f}°C")
        print(f"Мин. температура: {np.min(raw_arr):.3f}°C")
        print(f"Макс. температура: {np.max(raw_arr):.3f}°C")
        print(f"Размах: {np.max(raw_arr) - np.min(raw_arr):.3f}°C")
        print("-" * 50)
        print("АНАЛИЗ ШУМА")
        print("-" * 50)
        print(f"Средний шум: {np.mean(noise_arr):.4f}°C")
        print(f"СКО шума: {np.std(noise_arr):.4f}°C")
        print(f"Макс. выброс: {np.max(np.abs(noise_arr)):.4f}°C")
        print(f"Выбросов >0.2°C: {np.sum(np.abs(noise_arr) > 0.2)} "
              f"({np.sum(np.abs(noise_arr) > 0.2) / len(noise_arr) * 100:.1f}%)")
        print("=" * 50)