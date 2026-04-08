import serial
import csv
import time
from datetime import datetime
import matplotlib.pyplot as plt
from collections import deque
import numpy as np
import threading

# --- НАСТРОЙКИ ---
PORT = 'COM3'  # Замените на ваш COM-порт
BAUD_RATE = 9600
FILE_NAME = 'temperature_emulator_test.csv'
PLOT_WINDOW = 120  # Увеличим окно для тестов

# Настройки фильтров
MEDIAN_WINDOW = 5
EMA_ALPHA = 0.3
USE_KALMAN = True


# -----------------

class TemperatureFilter:
    """Класс для фильтрации температуры"""

    def __init__(self):
        self.median_buffer = deque(maxlen=MEDIAN_WINDOW)
        self.ema_value = None

        # Фильтр Калмана
        self.kalman_q = 0.01
        self.kalman_r = 0.1
        self.kalman_p = 1.0
        self.kalman_x = None
        self.kalman_k = 0

    def median_filter(self, value):
        self.median_buffer.append(value)
        if len(self.median_buffer) == MEDIAN_WINDOW:
            return sorted(self.median_buffer)[MEDIAN_WINDOW // 2]
        return value

    def ema_filter(self, value):
        if self.ema_value is None:
            self.ema_value = value
        else:
            self.ema_value = EMA_ALPHA * value + (1 - EMA_ALPHA) * self.ema_value
        return self.ema_value

    def kalman_filter(self, value):
        if self.kalman_x is None:
            self.kalman_x = value
            return value

        self.kalman_p = self.kalman_p + self.kalman_q
        self.kalman_k = self.kalman_p / (self.kalman_p + self.kalman_r)
        self.kalman_x = self.kalman_x + self.kalman_k * (value - self.kalman_x)
        self.kalman_p = (1 - self.kalman_k) * self.kalman_p

        return self.kalman_x

    def filter(self, raw_value):
        filtered = self.median_filter(raw_value)
        if USE_KALMAN:
            filtered = self.kalman_filter(filtered)
        else:
            filtered = self.ema_filter(filtered)
        return filtered


def send_command(ser, command):
    """Отправка команды эмулятору в отдельном потоке"""
    try:
        ser.write(command.encode())
        time.sleep(0.1)
        # Читаем ответ эмулятора (если есть)
        while ser.in_waiting:
            response = ser.readline().decode('utf-8', errors='ignore').strip()
            if response:
                print(f"[Эмулятор] {response}")
    except Exception as e:
        print(f"Ошибка отправки команды: {e}")


def command_thread_func(ser):
    """Поток для ручного управления эмулятором"""
    print("\n=== УПРАВЛЕНИЕ ЭМУЛЯТОРОМ ===")
    print("Доступные команды:")
    print("  0-7 - Выбор режима эмуляции")
    print("  ?   - Показать справку")
    print("  q   - Выйти из режима управления")
    print("================================\n")

    while True:
        try:
            cmd = input("Команда > ").strip()
            if cmd.lower() == 'q':
                break
            elif cmd:
                send_command(ser, cmd)
        except EOFError:
            break
        except KeyboardInterrupt:
            break


def read_temperature(ser):
    """Чтение температуры с пропуском текстовых сообщений"""
    timeout = time.time() + 2  # Таймаут 2 секунды

    while time.time() < timeout:
        if ser.in_waiting:
            line = ser.readline().decode('utf-8', errors='ignore').strip()

            if not line:
                continue

            # Пропускаем текстовые сообщения эмулятора
            if (line.startswith("Эмулятор") or
                    line.startswith("Режим") or
                    line.startswith("===") or
                    line.startswith("Команды") or
                    line.startswith("Ступень") or
                    "запущен" in line):
                print(f"[Эмулятор] {line}")
                continue

            # Пробуем преобразовать в число
            try:
                return float(line)
            except ValueError:
                # Если не число - выводим как информационное сообщение
                print(f"[Эмулятор] {line}")
                continue

    return None  # Таймаут


# Создаём фильтр
temp_filter = TemperatureFilter()

# Настройка графиков
plt.ion()
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
fig.suptitle('Тестирование фильтров на эмуляторе DS18B20')

ax1.set_xlabel('Время (сек)')
ax1.set_ylabel('Температура (°C)')
ax1.set_title('Сырые и фильтрованные данные')
ax1.grid(True, alpha=0.3)
raw_line, = ax1.plot([], [], 'r-', alpha=0.5, label='Сырые', linewidth=1)
filtered_line, = ax1.plot([], [], 'b-', label='Фильтрованные', linewidth=2)
ax1.legend()

ax2.set_xlabel('Время (сек)')
ax2.set_ylabel('Разница (°C)')
ax2.set_title('Уровень шума (сырые - фильтрованные)')
ax2.grid(True, alpha=0.3)
noise_line, = ax2.plot([], [], 'g-', alpha=0.7, linewidth=1)
ax2.axhline(y=0, color='k', linestyle='--', alpha=0.3)

# Данные для графиков
time_data = []
raw_data = []
filtered_data = []
noise_data = []

with open(FILE_NAME, 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['Timestamp', 'Raw_Temp', 'Filtered_Temp', 'Noise', 'Mode'])

    ser = None
    try:
        ser = serial.Serial(PORT, BAUD_RATE, timeout=1)
        time.sleep(2)
        ser.flushInput()

        # Запрашиваем справку от эмулятора
        send_command(ser, '?')

        print(f"\nСоединение с {PORT} установлено.")
        print("Запуск потока управления эмулятором...")

        # Запускаем поток для ручного управления
        cmd_thread = threading.Thread(target=command_thread_func, args=(ser,), daemon=True)
        cmd_thread.start()

        print("Логирование начато. Для остановки нажмите Ctrl+C")
        print("Используйте поток управления для смены режимов эмулятора.\n")

        current_mode = "?"
        measurement_count = 0

        while True:
            try:
                # Очищаем буфер перед запросом (на случай мусора)
                ser.flushInput()

                # Запрос у эмулятора
                ser.write(b'T')
                request_time = datetime.now()

                # Чтение ответа с фильтрацией текстовых сообщений
                raw_temp = read_temperature(ser)

                if raw_temp is not None:
                    measurement_count += 1

                    # Применяем фильтрацию
                    filtered_temp = temp_filter.filter(raw_temp)
                    noise = raw_temp - filtered_temp

                    # Сохраняем в CSV
                    writer.writerow([
                        request_time.isoformat(),
                        f"{raw_temp:.3f}",
                        f"{filtered_temp:.3f}",
                        f"{noise:.3f}",
                        current_mode
                    ])
                    csvfile.flush()

                    # Обновляем данные для графиков
                    current_time = time.time()
                    time_data.append(current_time)
                    raw_data.append(raw_temp)
                    filtered_data.append(filtered_temp)
                    noise_data.append(noise)

                    # Ограничиваем окно отображения
                    if len(time_data) > 0:
                        plot_time = [t - time_data[0] for t in time_data][-PLOT_WINDOW:]
                        plot_raw = raw_data[-PLOT_WINDOW:]
                        plot_filtered = filtered_data[-PLOT_WINDOW:]
                        plot_noise = noise_data[-PLOT_WINDOW:]

                        # Обновляем линии
                        raw_line.set_xdata(plot_time)
                        raw_line.set_ydata(plot_raw)
                        filtered_line.set_xdata(plot_time)
                        filtered_line.set_ydata(plot_filtered)
                        noise_line.set_xdata(plot_time)
                        noise_line.set_ydata(plot_noise)

                        # Автомасштабирование
                        ax1.relim()
                        ax1.autoscale_view()
                        ax2.relim()
                        ax2.autoscale_view()

                        fig.canvas.draw()
                        fig.canvas.flush_events()

                    # Вывод в консоль (каждое 10-е измерение или если есть шум)
                    if measurement_count % 10 == 0 or abs(noise) > 0.2:
                        print(f"[{request_time.strftime('%H:%M:%S')}] "
                              f"Измерение #{measurement_count} | "
                              f"Сырые: {raw_temp:.3f}°C → "
                              f"Фильтр: {filtered_temp:.3f}°C "
                              f"(шум: {noise:+.3f}°C)")
                else:
                    print(f"[{request_time.strftime('%H:%M:%S')}] Пропуск измерения: нет ответа от датчика")

                time.sleep(1)

            except ValueError as e:
                print(f"Ошибка значения: {e}")
                time.sleep(1)
            except KeyboardInterrupt:
                print("\nЛогирование остановлено пользователем.")
                break
            except Exception as e:
                print(f"Неожиданная ошибка: {e}")
                time.sleep(1)

    except serial.SerialException as e:
        print(f"Ошибка открытия порта {PORT}: {e}")
        print("Проверьте:")
        print("  1. Правильно ли указан COM-порт")
        print("  2. Не занят ли порт другой программой")
        print("  3. Подключена ли Arduino")
    finally:
        if ser and ser.is_open:
            ser.close()
            print("Соединение с Serial-портом закрыто.")

# Статистика по шуму
if noise_data:
    noise_array = np.array(noise_data)
    print(f"\n=== СТАТИСТИКА ШУМА ===")
    print(f"Количество измерений: {len(noise_data)}")
    print(f"Среднее значение шума: {np.mean(noise_array):.4f}°C")
    print(f"СКО шума: {np.std(noise_array):.4f}°C")
    print(f"Максимальный выброс: {np.max(np.abs(noise_array)):.4f}°C")
    print(f"Процент выбросов >0.2°C: {np.sum(np.abs(noise_array) > 0.2) / len(noise_array) * 100:.1f}%")

print(f"\nДанные сохранены в файл: {FILE_NAME}")
print("Закройте окно графика для завершения программы.")

# Блокируем окно графика до закрытия пользователем
plt.ioff()
plt.show(block=True)