import threading
import time

from logHandler import log

from .repository import TimerRepository
from .schema import TimerSchema
from .timer import Timer


def _with_lock(func):
    def wrapper(self, *args, **kwargs):
        with self._lock:
            return func(self, *args, **kwargs)

    return wrapper


class TimerManager:
    TIMER_NAME_TEMPLATE = "Timer {n}"

    def __init__(self, config: TimerRepository):
        self._config = config
        self.timers = [Timer(config, self) for config in config.get_timers()]
        self._run_thread = None
        self._event = threading.Event()
        self._lock = threading.Lock()
        self._terminate = False
        self._update_callbacks = set()
        self.last_input_timestamp = time.time()

    def start(self):
        if self._run_thread is not None:
            raise RuntimeError("Timer manager is already running")
        self._terminate = False
        self._run_thread = threading.Thread(target=self._run)
        self._run_thread.start()

    def stop(self):
        if self._run_thread is None:
            raise RuntimeError("Timer manager is not running")
        self._terminate = True
        self._event.set()
        self._run_thread.join()
        self._run_thread = None

    @property
    def enabled_timers(self) -> list[Timer]:
        return [t for t in self.timers if t.enabled]

    def _run(self):
        delay = 0
        while True:
            if self._event.wait(delay):
                self._event.clear()
            if self._terminate:
                return
            delay = self._update()

    @_with_lock
    def _update(self) -> int | None:
        next_timer = None
        next_timer_action_timestamp = None
        delay = None
        changed = False
        i = 0
        while i < len(self.timers):
            timer = self.timers[i]
            if timer.should_be_removed:
                del self.timers[i]
                self._config.remove_timer(timer.config.id)
                changed = True
                continue
            action_timestamp = timer.next_action_time
            if action_timestamp is not None and (
                next_timer is None or action_timestamp < next_timer_action_timestamp
            ):
                next_timer = timer
                next_timer_action_timestamp = action_timestamp
            i += 1
        if next_timer is not None:
            timestamp = time.time()
            delay = next_timer_action_timestamp - timestamp
            if delay > 0:
                delay = min(delay, 30)
            else:
                next_timer.do_next_action()
                if next_timer.should_be_removed:
                    self.timers.remove(next_timer)
                    self._config.remove_timer(next_timer.config.id)
                else:
                    self._config.update_timer(next_timer.config)
                changed = True
        if changed:
            self._config.save()
            self._trigger_update()
        return delay

    @_with_lock
    def add_timer(self, timer: TimerSchema):
        new_timer = Timer(timer, self)
        new_timer.reset()
        self._config.add_timer(timer)
        self.timers.append(new_timer)
        self._config.save()
        self._trigger_update()

    @_with_lock
    def remove_timer(self, timer_id: int):
        removed = False
        for i, timer in enumerate(self.timers):
            if timer.config.id == timer_id:
                del self.timers[i]
                removed = True
                break
        if not removed:
            raise ValueError(f"Timer with id {timer_id} not found")
        self._config.remove_timer(timer_id)
        self._config.save()
        self._trigger_update()

    def get_timer(self, timer_id: int) -> Timer | None:
        for timer in self.timers:
            if timer.config.id == timer_id:
                return timer

    def update_timer(self, timer: Timer):
        self._config.update_timer(timer.config)
        self._trigger_update()

    def _trigger_update(self):
        self._run_update_callbacks()
        self._config.save()
        self._event.set()

    def register_update_callback(self, callback: callable):
        self._update_callbacks.add(callback)

    def unregister_update_callback(self, callback: callable):
        self._update_callbacks.discard(callback)

    def _run_update_callbacks(self):
        for callback in self._update_callbacks:
            try:
                callback()
            except Exception:
                log.exception("Exception in update callback:")

    def generate_timer_name(self):
        names = set(t.config.name for t in self.timers)
        n = 1
        while True:
            name = self.TIMER_NAME_TEMPLATE.format(n=n)
            if name not in names:
                return name
            n += 1

    def handle_input(self):
        self.last_input_timestamp = time.time()
