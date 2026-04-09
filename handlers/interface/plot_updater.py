"""Обработчик: обновление графиков с кнопкой выхода и обработкой закрытия окна"""

import matplotlib.pyplot as plt

from events import EventType, TemperatureEvent
from . import plot_config as config
from ._time_formatter import _apply_time_formatter
from ._plot_widgets import _PlotWidgets
from ._data_plots import _DataPlots
import config as app_config  # ваш основной config


class PlotUpdater:
    """Обновление графиков в реальном времени с кнопкой выхода"""

    def __init__(self, window_size: int = None, on_exit_callback=None):
        self.window_size = window_size or app_config.PLOT_WINDOW
        self.time_data = []
        self.raw_data = []
        self.filtered_data = []
        self.noise_data = []
        self.on_exit_callback = on_exit_callback
        self.exit_requested = False
        self.window_closed = False
        self._setup_plot()

    def _setup_plot(self):
        """Настройка графиков с кнопкой выхода"""
        plt.ion()

        # Создаём фигуру
        self.fig = plt.figure(figsize=config.FIGURE_SIZE)

        # Подключаем обработчик закрытия окна (крестик)
        self.fig.canvas.mpl_connect('close_event', self._on_window_closed)

        # Создаём графики
        self._plots = _DataPlots(self.fig)

        # Создаём виджеты
        self._widgets = _PlotWidgets(self.fig)
        self._widgets.set_exit_callback(self._on_exit_clicked)

        # Добавляем место для кнопки снизу
        plt.subplots_adjust(bottom=config.BOTTOM_PADDING)

    def _on_window_closed(self, event):
        """Обработчик закрытия окна (крестик)"""
        if not self.exit_requested and not self.window_closed:
            print("\n[Plot] Окно графика закрыто (крестик).")
            self.window_closed = True
            self._request_exit()

    def _on_exit_clicked(self, event):
        """Обработчик нажатия кнопки выхода"""
        if not self.exit_requested and not self.window_closed:
            print("\n[Plot] Нажата кнопка завершения...")
            self._request_exit()

    def _request_exit(self):
        """Запрос на завершение программы"""
        self.exit_requested = True

        # Обновляем визуальное состояние если окно ещё открыто
        try:
            if plt.fignum_exists(self.fig.number):
                self._widgets.update_exit_button('⏳ Завершение...', 'gray')
                self._widgets.update_info_text('Завершение программы...')
                self.fig.canvas.draw()
        except:
            pass

        # Вызываем внешний callback если есть
        if self.on_exit_callback:
            import threading
            thread = threading.Thread(target=self.on_exit_callback, daemon=True)
            thread.start()

    async def handle_temperature(self, event: TemperatureEvent):
        """Обработка события температуры"""
        if self.window_closed or self.exit_requested:
            return

        if event.type == EventType.TEMPERATURE_FILTERED:
            data = event.data
            current_time = event.timestamp.timestamp()

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
            self._plots.update_lines(
                self.time_data, self.raw_data,
                self.filtered_data, self.noise_data
            )

            # Применяем форматтер времени
            ax1, ax2 = self._plots.get_axes()
            _apply_time_formatter(ax1, ax2)

            # Отрисовка (с проверкой что окно ещё существует)
            self.fig.autofmt_xdate(rotation=config.TIME_ROTATION)
            try:
                if plt.fignum_exists(self.fig.number):
                    self.fig.canvas.draw()
                    self.fig.canvas.flush_events()
            except:
                self.window_closed = True

    def is_window_alive(self) -> bool:
        """Проверяет, открыто ли ещё окно графика"""
        try:
            return plt.fignum_exists(self.fig.number)
        except:
            return False

    def show_blocking(self):
        """Показать график и ждать закрытия"""
        plt.ioff()
        plt.show(block=True)

    def close(self):
        """Закрыть окно графика"""
        try:
            if plt.fignum_exists(self.fig.number):
                plt.close(self.fig)
        except:
            pass