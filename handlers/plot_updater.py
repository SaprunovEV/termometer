"""Обработчик: обновление графиков с кнопкой выхода и обработкой закрытия окна"""

import time
import asyncio
import matplotlib.pyplot as plt
from matplotlib.widgets import Button

from events import EventType, TemperatureEvent
import config


class PlotUpdater:
    """Обновление графиков в реальном времени с кнопкой выхода"""

    def __init__(self, window_size: int = None, on_exit_callback=None):
        self.window_size = window_size or config.PLOT_WINDOW
        self.time_data = []
        self.raw_data = []
        self.filtered_data = []
        self.noise_data = []
        self.start_time = time.time()
        self.on_exit_callback = on_exit_callback  # Callback для завершения
        self.exit_requested = False
        self.window_closed = False
        self._setup_plot()

    def _setup_plot(self):
        """Настройка графиков с кнопкой выхода"""
        plt.ion()

        # Создаём фигуру
        self.fig = plt.figure(figsize=(12, 9))

        # Подключаем обработчик закрытия окна (крестик)
        self.fig.canvas.mpl_connect('close_event', self._on_window_closed)

        # Графики занимают верхнюю часть
        self.ax1 = plt.subplot(2, 1, 1)
        self.ax2 = plt.subplot(2, 1, 2)

        self.fig.suptitle('Мониторинг температуры (событийная архитектура)', fontsize=14)

        # Настройка первого графика
        self.ax1.set_xlabel('Время (сек)')
        self.ax1.set_ylabel('Температура (°C)')
        self.ax1.set_title('Сырые и фильтрованные данные')
        self.ax1.grid(True, alpha=0.3)
        self.raw_line, = self.ax1.plot([], [], 'r-', alpha=0.5, label='Сырые', linewidth=1)
        self.filt_line, = self.ax1.plot([], [], 'b-', label='Фильтрованные', linewidth=2)
        self.ax1.legend(loc='upper right')

        # Настройка второго графика
        self.ax2.set_xlabel('Время (сек)')
        self.ax2.set_ylabel('Разница (°C)')
        self.ax2.set_title('Уровень шума')
        self.ax2.grid(True, alpha=0.3)
        self.noise_line, = self.ax2.plot([], [], 'g-', alpha=0.7, linewidth=1)
        self.ax2.axhline(y=0, color='k', linestyle='--', alpha=0.3)

        # Добавляем место для кнопки снизу
        plt.subplots_adjust(bottom=0.1)

        # Создаём область для кнопки завершения
        button_ax = plt.axes([0.35, 0.02, 0.2, 0.05])
        self.exit_button = Button(button_ax, '🛑 ЗАВЕРШИТЬ', color='lightcoral', hovercolor='red')
        self.exit_button.on_clicked(self._on_exit_clicked)

        # Добавляем информационную панель
        info_ax = plt.axes([0.58, 0.02, 0.4, 0.05])
        info_ax.set_axis_off()
        self.info_text = info_ax.text(0, 0.5, 'Крестик окна | Ctrl+C | Кнопка',
                                      transform=info_ax.transAxes, va='center',
                                      fontsize=9, color='gray')

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
                self.exit_button.label.set_text('⏳ Завершение...')
                self.exit_button.color = 'gray'
                self.exit_button.hovercolor = 'gray'
                self.info_text.set_text('Завершение программы...')
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
        # Если окно закрыто или запрошен выход - не обновляем
        if self.window_closed or self.exit_requested:
            return

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

            # Отрисовка (с проверкой что окно ещё существует)
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