"""Внутреннее управление линиями графиков"""

import matplotlib.pyplot as plt
from . import plot_config as config


class _DataPlots:
    """Управление отображением данных на графиках"""

    def __init__(self, fig):
        self.fig = fig
        self.ax1 = None
        self.ax2 = None
        self.raw_line = None
        self.filt_line = None
        self.noise_line = None
        self._setup_axes()
        self._setup_lines()

    def _setup_axes(self):
        """Настройка осей"""
        self.ax1 = plt.subplot(2, 1, 1)
        self.ax2 = plt.subplot(2, 1, 2)

        self.fig.suptitle(config.FIGURE_TITLE, fontsize=14)

        # Настройка первого графика
        self.ax1.set_xlabel(config.X_LABEL)
        self.ax1.set_ylabel(config.Y_LABEL_TEMP)
        self.ax1.set_title(config.AX1_TITLE)
        self.ax1.grid(True, alpha=config.GRID_ALPHA)

        # Настройка второго графика
        self.ax2.set_xlabel(config.X_LABEL)
        self.ax2.set_ylabel(config.Y_LABEL_NOISE)
        self.ax2.set_title(config.AX2_TITLE)
        self.ax2.grid(True, alpha=config.GRID_ALPHA)
        self.ax2.axhline(y=0, color='k', linestyle='--', alpha=0.3)

    def _setup_lines(self):
        """Настройка линий"""
        # Линии первого графика
        self.raw_line, = self.ax1.plot(
            [], [], config.RAW_LINE_COLOR,
            alpha=config.RAW_LINE_ALPHA,
            label='Сырые',
            linewidth=config.RAW_LINE_WIDTH
        )
        self.filt_line, = self.ax1.plot(
            [], [], config.FILT_LINE_COLOR,
            label='Фильтрованные',
            linewidth=config.FILT_LINE_WIDTH
        )
        self.ax1.legend(loc='upper right')

        # Линия второго графика
        self.noise_line, = self.ax2.plot(
            [], [], config.NOISE_LINE_COLOR,
            alpha=config.NOISE_LINE_ALPHA,
            linewidth=config.NOISE_LINE_WIDTH
        )

    def update_lines(self, time_data, raw_data, filtered_data, noise_data):
        """Обновление данных на линиях"""
        self.raw_line.set_xdata(time_data)
        self.raw_line.set_ydata(raw_data)
        self.filt_line.set_xdata(time_data)
        self.filt_line.set_ydata(filtered_data)
        self.noise_line.set_xdata(time_data)
        self.noise_line.set_ydata(noise_data)

        # Автомасштабирование
        self.ax1.relim()
        self.ax1.autoscale_view()
        self.ax2.relim()
        self.ax2.autoscale_view()

    def get_axes(self):
        """Возвращает оси для применения форматтера"""
        return self.ax1, self.ax2