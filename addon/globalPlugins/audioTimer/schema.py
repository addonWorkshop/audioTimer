from dataclasses import dataclass
from enum import Enum
from inspect import isclass

from .enums import NotificationType, RestartPolicy, TimerFinishAction, TimerState


@dataclass
class TimerSchema:
    name: str
    interval: int
    repeat_limit: int
    finish_action: TimerFinishAction
    notification_type: NotificationType
    recurrent_notification_interval: int
    restart_policy: RestartPolicy
    id: int | None = None
    state: TimerState = TimerState.ACTIVE
    finish_time: float = 0
    repeat_count: int = 0
    recurrent_notification_time: float = 0
    recurrent_notification_repeat_limit_after_input: int = 0
    recurrent_notification_repeat_count_after_input: int = 0
    recurrent_notification_last_input_timestamp: float = 0
    notification_sound: str = ""

    def __post_init__(self):
        # Enum attributes converted to values (strings) after initialization,
        # so we need to convert them back to the actual enums.
        for attr_name, attr_type in self.__annotations__.items():
            # Unions are not classes, so we need to check if it's a class
            if isclass(attr_type) and issubclass(attr_type, Enum):
                setattr(self, attr_name, attr_type(getattr(self, attr_name)))
