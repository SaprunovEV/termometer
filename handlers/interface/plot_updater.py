"""Обработчик: обновление графиков с кнопкой выхода и обработкой закрытия окна"""

import matplotlib.pyplot as plt
import serial.tools.list_ports

from events import EventType, TemperatureEvent
from . import plot_config as config
from ._time_formatter import _apply_time_formatter
from ._plot_widgets import _PlotWidgets
from ._data_plots import _DataPlots
import config as app_config  # ваш основной config


class PlotUpdater:
    """Обновление графиков в реальном времени с кнопкой выхода и выбором COM порта"""

    def __init__(self, window_size: int = None, on_exit_callback=None, on_port_selected_callback=None):
        self.window_size = window_size or app_config.PLOT_WINDOW
        self.time_data = []
        self.raw_data = []
        self.filtered_data = []
        self.noise_data = []
        self.on_exit_callback = on_exit_callback
        self.on_port_selected_callback = on_port_selected_callback
        self.exit_requested = False
        self.window_closed = False
        self.selected_port = None
        self._setup_plot()

    def _setup_plot(self):
        """Настройка графиков с кнопкой выхода и выбором COM порта"""
        plt.ion()

        # Создаём фигуру
        self.fig = plt.figure(figsize=config.FIGURE_SIZE)

        # Подключаем обработчик закрытия окна (крестик)
        self.fig.canvas.mpl_connect('close_event', self._on_window_closed)

        # Создаём графики
        self._plots = _DataPlots(self.fig)

        # Создаём виджеты (здесь нужно будет расширить _PlotWidgets)
        self._widgets = _PlotWidgets(self.fig)
        self._widgets.set_exit_callback(self._on_exit_clicked)

        # Добавляем виджет для выбора COM порта
        self._setup_com_port_selector()

        # Добавляем место для кнопки и селектора снизу
        plt.subplots_adjust(bottom=config.BOTTOM_PADDING)

    def _setup_com_port_selector(self):
        """Создание выпадающего списка для выбора COM порта"""
        from matplotlib.widgets import RadioButtons

        # Получаем список доступных COM портов
        available_ports = self._get_available_com_ports()

        if not available_ports:
            available_ports = ["Нет доступных портов"]

        # Позиция для селектора (можно настроить)
        selector_ax = plt.axes([0.7, 0.02, 0.25, 0.04])

        # Создаем выпадающий список с помощью RadioButtons
        self.com_selector = RadioButtons(
            selector_ax,
            available_ports,
            active=0
        )

        # Настройка внешнего вида селектора
        selector_ax.set_title("COM порт", fontsize=8)

        # Подключаем обработчик выбора порта
        self.com_selector.on_clicked(self._on_port_selected)

        # Сохраняем ссылку на ось для обновления
        self.selector_ax = selector_ax

    def _get_available_com_ports(self):
        """Получение списка доступных COM портов"""
        ports = serial.tools.list_ports.comports()
        port_list = [f"{port.device} - {port.description}" for port in ports]
        return port_list if port_list else []

    def _on_port_selected(self, label):
        """Обработчик выбора COM порта"""
        if "Нет доступных портов" in label:
            print("[Plot] Нет доступных COM портов")
            return

        # Извлекаем имя порта из выбранной метки
        port_name = label.split(" - ")[0] if " - " in label else label
        self.selected_port = port_name

        print(f"\n[Plot] Выбран COM порт: {port_name}")

        # Обновляем информационную метку
        try:
            if plt.fignum_exists(self.fig.number):
                self._widgets.update_info_text(f'Выбран порт: {port_name}')
                self.fig.canvas.draw()
        except:
            pass

        # Вызываем callback если есть
        if self.on_port_selected_callback:
            import threading
            thread = threading.Thread(
                target=self.on_port_selected_callback,
                args=(port_name,),
                daemon=True
            )
            thread.start()

    def refresh_com_ports(self):
        """Обновление списка COM портов"""
        available_ports = self._get_available_com_ports()

        if not available_ports:
            available_ports = ["Нет доступных портов"]

        # Обновляем список в селекторе
        self.com_selector.labels.clear()
        self.com_selector.circles = []
        self.com_selector.value_selected = None

        for label in available_ports:
            self.com_selector.labels.append(
                self.com_selector.ax.text(
                    0.25,
                    0.5,
                    label,
                    transform=self.com_selector.ax.transAxes,
                    ha="left",
                    va="center"
                )
            )
            self.com_selector.circles.append(
                plt.Circle(
                    (0.15, 0.5),
                    0.07,
                    transform=self.com_selector.ax.transAxes,
                    fc='white',
                    ec='black',
                    lw=1
                )
            )
            self.com_selector.ax.add_artist(self.com_selector.circles[-1])

        if available_ports:
            self.com_selector.active = 0
            self.com_selector.eventson = False
            self.com_selector.value_selected = available_ports[0]
            self.com_selector.eventson = True
            self.com_selector._active = 0
            for i, circle in enumerate(self.com_selector.circles):
                circle.set_facecolor('black' if i == 0 else 'white')

        # Перерисовываем
        try:
            if plt.fignum_exists(self.fig.number):
                self.fig.canvas.draw()
        except:
            pass

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
            self.raw_data.append(data[0].value)
            self.filtered_data.append(data[0].filtered)
            self.noise_data.append(data[0].noise())

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

    def get_selected_port(self) -> str:
        """Возвращает выбранный COM порт"""
        return self.selected_port

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