"""Левая панель с текущими данными"""

import matplotlib.pyplot as plt
from . import plot_config as config


class _LeftPanel:
    """Левая панель для отображения текущих данных"""

    def __init__(self, fig, gs):
        self.fig = fig
        self.gs = gs
        self.ax = None
        self.text_elements = {}
        self._setup_panel()

    def _setup_panel(self):
        """Настройка левой панели"""
        # Создаём область для левой панели
        self.ax = plt.subplot(self.gs[0, 0])
        self.ax.set_facecolor(config.LEFT_PANEL_BG_COLOR)
        self.ax.set_title(
            config.LEFT_PANEL_TITLE,
            fontsize=config.LEFT_PANEL_TITLE_FONTSIZE,
            fontweight='bold',
            pad=20
        )
        self.ax.axis('off')  # Убираем оси

        # Создаём текстовые поля для отображения данных
        self._create_text_fields()

    def _create_text_fields(self):
        """Создание текстовых полей"""
        text_props = dict(
            fontsize=config.TEXT_FONTSIZE,
            fontfamily=config.TEXT_FONTFAMILY,
            bbox=config.TEXT_BOX_STYLE
        )

        # Время последнего обновления
        self.text_elements['time'] = self.ax.text(
            0.1, 0.85, 'Время: --:--:--',
            transform=self.ax.transAxes, **text_props
        )

        # ИСПРАВЛЕНО: рисуем разделительную линию с помощью plot
        # Разделительная линия после времени
        x_start, x_end = 0.05, 0.95
        y_line = 0.8
        self.ax.plot(
            [x_start, x_end], [y_line, y_line],
            color='gray', linewidth=1,
            transform=self.ax.transAxes
        )

        # Сырая температура
        self.text_elements['raw'] = self.ax.text(
            0.1, 0.7, 'Сырая: --.-- °C',
            transform=self.ax.transAxes, **text_props
        )

        # Фильтрованная температура
        self.text_elements['filtered'] = self.ax.text(
            0.1, 0.55, 'Фильтрованная: --.-- °C',
            transform=self.ax.transAxes, **text_props
        )

        # Уровень шума
        self.text_elements['noise'] = self.ax.text(
            0.1, 0.4, 'Шум: --.--- °C',
            transform=self.ax.transAxes, **text_props
        )

        # ИСПРАВЛЕНО: вторая разделительная линия
        y_line2 = 0.35
        self.ax.plot(
            [x_start, x_end], [y_line2, y_line2],
            color='gray', linewidth=1,
            transform=self.ax.transAxes
        )

        # Статус
        self.text_elements['status'] = self.ax.text(
            0.1, 0.25, 'Статус: Активен',
            transform=self.ax.transAxes, **text_props
        )

        # Количество точек
        self.text_elements['points'] = self.ax.text(
            0.1, 0.1, 'Точек: 0',
            transform=self.ax.transAxes, **text_props
        )

    def update_data(self, timestamp, raw, filtered, noise, points_count, is_active=True):
        """Обновление отображаемых данных"""
        # Обновляем время
        time_str = timestamp.strftime('%H:%M:%S') if timestamp else '--:--:--'
        self.text_elements['time'].set_text(f'Время: {time_str}')

        # Обновляем температуру
        self.text_elements['raw'].set_text(f'Сырая: {raw:.2f} °C')
        self.text_elements['filtered'].set_text(f'Фильтрованная: {filtered:.2f} °C')
        self.text_elements['noise'].set_text(f'Шум: {noise:.3f} °C')

        # Обновляем статус
        status_text = 'Статус: Активен' if is_active else 'Статус: Завершение...'
        self.text_elements['status'].set_text(status_text)

        # Обновляем количество точек
        self.text_elements['points'].set_text(f'Точек: {points_count}')

    def update_status(self, is_active):
        """Обновление только статуса"""
        status_text = 'Статус: Активен' if is_active else 'Статус: Завершение...'
        self.text_elements['status'].set_text(status_text)

    def get_ax(self):
        """Возвращает ось левой панели"""
        return self.ax