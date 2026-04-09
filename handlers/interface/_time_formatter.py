"""Внутренний форматтер для отображения времени на осях"""

from datetime import datetime
import matplotlib.pyplot as plt


def _time_formatter(x, pos):
    """Преобразует timestamp в строку HH:MM:SS"""
    try:
        dt = datetime.fromtimestamp(x)
        return dt.strftime('%H:%M:%S')
    except:
        return ''


def _apply_time_formatter(ax1, ax2):
    """Применяет форматтер времени к осям"""
    formatter = plt.FuncFormatter(_time_formatter)
    ax1.xaxis.set_major_formatter(formatter)
    ax2.xaxis.set_major_formatter(formatter)