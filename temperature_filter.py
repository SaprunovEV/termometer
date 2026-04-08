"""Фильтры для обработки температурных данных"""

from collections import deque
import config


class TemperatureFilter:
    """Комбинированный фильтр температуры"""

    def __init__(self):
        self.median_buffer = deque(maxlen=config.MEDIAN_WINDOW)
        self.ema_value = None

        # Параметры фильтра Калмана
        self.kalman_q = 0.01
        self.kalman_r = 0.1
        self.kalman_p = 1.0
        self.kalman_x = None
        self.kalman_k = 0

    def median_filter(self, value: float) -> float:
        """Медианный фильтр для удаления выбросов"""
        self.median_buffer.append(value)
        if len(self.median_buffer) == config.MEDIAN_WINDOW:
            return sorted(self.median_buffer)[config.MEDIAN_WINDOW // 2]
        return value

    def ema_filter(self, value: float) -> float:
        """Экспоненциальное скользящее среднее"""
        if self.ema_value is None:
            self.ema_value = value
        else:
            self.ema_value = config.EMA_ALPHA * value + (1 - config.EMA_ALPHA) * self.ema_value
        return self.ema_value

    def kalman_filter(self, value: float) -> float:
        """Упрощённый фильтр Калмана"""
        if self.kalman_x is None:
            self.kalman_x = value
            return value

        self.kalman_p = self.kalman_p + self.kalman_q
        self.kalman_k = self.kalman_p / (self.kalman_p + self.kalman_r)
        self.kalman_x = self.kalman_x + self.kalman_k * (value - self.kalman_x)
        self.kalman_p = (1 - self.kalman_k) * self.kalman_p

        return self.kalman_x

    def filter(self, raw_value: float) -> float:
        """Применить всю цепочку фильтров"""
        filtered = self.median_filter(raw_value)
        if config.USE_KALMAN:
            filtered = self.kalman_filter(filtered)
        else:
            filtered = self.ema_filter(filtered)
        return filtered