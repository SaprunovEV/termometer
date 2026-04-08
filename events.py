"""Классы событий системы"""

from enum import Enum
from datetime import datetime
from typing import Any


class EventType(Enum):
    """Типы событий"""
    TEMPERATURE_RAW = "temperature_raw"
    TEMPERATURE_FILTERED = "temperature_filtered"
    SENSOR_ERROR = "sensor_error"
    SYSTEM_STATUS = "system_status"
    MODE_CHANGED = "mode_changed"


class TemperatureEvent:
    """Событие с данными температуры"""

    def __init__(self, event_type: EventType, data: Any, timestamp: datetime = None):
        self.type = event_type
        self.data = data
        self.timestamp = timestamp or datetime.now()

    def __repr__(self):
        return f"TemperatureEvent({self.type.value}, {self.data}, {self.timestamp})"