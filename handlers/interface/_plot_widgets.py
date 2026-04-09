"""Внутренние виджеты для графиков"""

from matplotlib.widgets import Button
from . import plot_config as config


class _PlotWidgets:
    """Управление виджетами на графике"""

    def __init__(self, fig):
        self.fig = fig
        self.exit_button = None
        self.info_text = None
        self._setup_widgets()

    def _setup_widgets(self):
        """Настройка виджетов"""
        # Кнопка завершения
        button_ax = self.fig.add_axes(config.BUTTON_AX_POS)
        self.exit_button = Button(
            button_ax,
            config.BUTTON_TEXT,
            color=config.BUTTON_COLOR,
            hovercolor=config.BUTTON_HOVERCOLOR
        )

        # Информационная панель
        info_ax = self.fig.add_axes(config.INFO_AX_POS)
        info_ax.set_axis_off()
        self.info_text = info_ax.text(
            0, 0.5,
            config.INFO_TEXT,
            transform=info_ax.transAxes,
            va='center',
            fontsize=9,
            color='gray'
        )

    def set_exit_callback(self, callback):
        """Установка callback для кнопки выхода"""
        self.exit_button.on_clicked(callback)

    def update_exit_button(self, text, color):
        """Обновление состояния кнопки выхода"""
        self.exit_button.label.set_text(text)
        self.exit_button.color = color
        self.exit_button.hovercolor = color

    def update_info_text(self, text):
        """Обновление информационного текста"""
        self.info_text.set_text(text)