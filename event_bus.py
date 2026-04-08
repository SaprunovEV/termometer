"""Шина событий - центральный диспетчер"""

import asyncio
import queue
from typing import Dict, List, Callable

from events import EventType, TemperatureEvent


class EventBus:
    """Шина событий с поддержкой асинхронной обработки"""

    def __init__(self):
        self._subscribers: Dict[EventType, List[Callable]] = {
            event_type: [] for event_type in EventType
        }
        self._async_queue = queue.Queue()
        self._running = False

    def subscribe(self, event_type: EventType, callback: Callable):
        """Подписаться на событие"""
        self._subscribers[event_type].append(callback)
        print(f"[EventBus] + подписчик на {event_type.value}")

    def unsubscribe(self, event_type: EventType, callback: Callable):
        """Отписаться от события"""
        if callback in self._subscribers[event_type]:
            self._subscribers[event_type].remove(callback)
            print(f"[EventBus] - подписчик на {event_type.value}")

    async def emit(self, event: TemperatureEvent):
        """Асинхронно отправить событие всем подписчикам"""
        if event.type not in self._subscribers:
            return

        tasks = []
        for callback in self._subscribers[event.type]:
            if asyncio.iscoroutinefunction(callback):
                tasks.append(callback(event))
            else:
                tasks.append(asyncio.to_thread(callback, event))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    def emit_sync(self, event: TemperatureEvent):
        """Синхронная отправка (для вызова из других потоков)"""
        self._async_queue.put(event)

    async def process_events(self):
        """Обработка событий из очереди"""
        while self._running:
            try:
                while not self._async_queue.empty():
                    event = self._async_queue.get_nowait()
                    await self.emit(event)
                await asyncio.sleep(0.01)
            except Exception as e:
                print(f"[EventBus] Ошибка: {e}")

    def start(self):
        """Запуск обработки"""
        self._running = True

    def stop(self):
        """Остановка обработки"""
        self._running = False