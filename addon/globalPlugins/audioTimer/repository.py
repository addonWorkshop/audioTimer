import dataclasses
import json
from pathlib import Path

from .config.config import load_config, save_config
from .schema import TimerSchema


class TimerRepository:
    def __init__(self, config_path: Path):
        self._config_path = config_path
        self._config = load_config(self._config_path)

    def save(self):
        save_config(self._config_path, self._config)

    def get_timers(self):
        return [TimerSchema(**t) for t in self._config["timers"]]

    def add_timer(self, timer: TimerSchema):
        if timer.id is None:
            timer.id = self._config["next_timer_id"]
            self._config["next_timer_id"] += 1
        self._config["timers"].append(dataclasses.asdict(timer))

    def remove_timer(self, timer_id: int):
        for i, timer in enumerate(self._config["timers"]):
            if timer["id"] == timer_id:
                del self._config["timers"][i]
                break

    def update_timer(self, timer: TimerSchema):
        for i, t in enumerate(self._config["timers"]):
            if t["id"] == timer.id:
                self._config["timers"][i] = dataclasses.asdict(timer)
                return
        raise ValueError(f"Timer with id {timer.id} not found")

    @property
    def ignored_keys(self):
        return self._config["ignored_keys"]
