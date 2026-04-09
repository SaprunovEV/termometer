"""Конфигурация для отображения графиков"""

# Настройки окна
FIGURE_SIZE = (12, 9)
FIGURE_TITLE = 'Мониторинг температуры (событийная архитектура)'

# Настройки осей
X_LABEL = 'Время (ЧЧ:ММ:СС)'
Y_LABEL_TEMP = 'Температура (°C)'
Y_LABEL_NOISE = 'Разница (°C)'

# Настройки первого графика
AX1_TITLE = 'Сырые и фильтрованные данные'
RAW_LINE_COLOR = 'r-'
RAW_LINE_ALPHA = 0.5
RAW_LINE_WIDTH = 1
FILT_LINE_COLOR = 'b-'
FILT_LINE_WIDTH = 2

# Настройки второго графика
AX2_TITLE = 'Уровень шума'
NOISE_LINE_COLOR = 'g-'
NOISE_LINE_ALPHA = 0.7
NOISE_LINE_WIDTH = 1

# Настройки кнопки
BUTTON_AX_POS = [0.35, 0.02, 0.2, 0.05]
BUTTON_TEXT = 'ЗАВЕРШИТЬ'
BUTTON_COLOR = 'lightcoral'
BUTTON_HOVERCOLOR = 'red'

# Информационная панель
INFO_AX_POS = [0.58, 0.02, 0.4, 0.05]
INFO_TEXT = 'Крестик окна | Ctrl+C | Кнопка'

# Общие настройки
GRID_ALPHA = 0.3
BOTTOM_PADDING = 0.1
TIME_ROTATION = 45