"""Конфигурация приложения"""

# Настройки Serial порта
PORT = 'COM3'
BAUD_RATE = 9600

# Настройки файлов
CSV_FILE = 'temperature_data.csv'

# Настройки графиков
PLOT_WINDOW = 120  # Количество точек на графике

# Настройки фильтров
MEDIAN_WINDOW = 5
EMA_ALPHA = 0.3
USE_KALMAN = True

# Настройки логирования
CONSOLE_LOG_INTERVAL = 10  # Вывод каждого N-го измерения