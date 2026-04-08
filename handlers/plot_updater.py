"""Обработчик: обновление графиков"""

import time
import matplotlib.pyplot as plt

from events import EventType, TemperatureEvent
import config


class PlotUpdater:
    """Обновление графиков в реальном времени"""

    def __init__(self, window_size: int = None):
        self.window_size = window_size or config.PLOT_WINDOW
        self.time_data = []
        self.raw_data = []
        self.filtered_data = []
        self.noise_data = []
        self.start_time = time.time()
        self._setup_plot()

    def _setup_plot(self):
        """Настройка графиков"""
        plt.ion()
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(12, 8))
        self.fig.suptitle('Мониторинг температуры (событийная архитектура)')

        self.ax1.set_xlabel('Время (сек)')
        self.ax1.set_ylabel('Температура (°C)')
        self.ax1.set_title('Сырые и фильтрованные данные')
        self.ax1.grid(True, alpha=0.3)
        self.raw_line, = self.ax1.plot([], [], 'r-', alpha=0.5, label='Сырые', linewidth=1)
        self.filt_line, = self.ax1.plot([], [], 'b-', label='Фильтрованные', linewidth=2)
        self.ax1.legend()

        self.ax2.set_xlabel('Время (сек)')
        self.ax2.set_ylabel('Разница (°C)')
        self.ax2.set_title('Уровень шума')
        self.ax2.grid(True, alpha=0.3)
        self.noise_line, = self.ax2.plot([], [], 'g-', alpha=0.7, linewidth=1)
        self.ax2.axhline(y=0, color='k', linestyle='--', alpha=0.3)

    async def handle_temperature(self, event: TemperatureEvent):
        """Обработка события температуры"""
        if event.type == EventType.TEMPERATURE_FILTERED:
            data = event.data
            current_time = time.time() - self.start_time

            self.time_data.append(current_time)
            self.raw_data.append(data['raw'])
            self.filtered_data.append(data['filtered'])
            self.noise_data.append(data['noise'])

            # Ограничиваем окно
            if len(self.time_data) > self.window_size:
                self.time_data = self.time_data[-self.window_size:]
                self.raw_data = self.raw_data[-self.window_size:]
                self.filtered_data = self.filtered_data[-self.window_size:]
                self.noise_data = self.noise_data[-self.window_size:]

            # Обновляем линии
            self.raw_line.set_xdata(self.time_data)
            self.raw_line.set_ydata(self.raw_data)
            self.filt_line.set_xdata(self.time_data)
            self.filt_line.set_ydata(self.filtered_data)
            self.noise_line.set_xdata(self.time_data)
            self.noise_line.set_ydata(self.noise_data)

            # Автомасштабирование
            self.ax1.relim()
            self.ax1.autoscale_view()
            self.ax2.relim()
            self.ax2.autoscale_view()

            # Отрисовка
            self.fig.canvas.draw()
            self.fig.canvas.flush_events()

    def show_blocking(self):
        """Показать график и ждать закрытия"""
        plt.ioff()
        plt.show(block=True)