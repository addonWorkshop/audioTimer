import time
from pathlib import Path

import addonHandler
import globalPluginHandler
import gui
import inputCore
import NVDAState
from scriptHandler import getLastScriptRepeatCount, script
from ui import message

from .enums import TimerState
from .repository import TimerRepository
from .timer_manager import TimerManager
from .ui.main_dialog import MainDialog
from .ui.new_timer_dialog import NewTimerDialog
from .ui.utils import show_dialog
from .utils import format_time

addonHandler.initTranslation()

CONFIG_PATH = Path(NVDAState.WritePaths.configDir) / "audioTimer.json"


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    scriptCategory = "Audio Timer"

    def __init__(self):
        super().__init__()
        self.config = TimerRepository(CONFIG_PATH)
        self.timer_manager = TimerManager(self.config)
        self.timer_manager.start()
        self._last_nearest_timer = None
        self._register()

    def terminate(self):
        self.timer_manager.stop()
        self._unregister()

    def _register(self):
        inputCore.decide_handleRawKey.register(self._decide_handle_raw_key)

    def _unregister(self):
        inputCore.decide_handleRawKey.unregister(self._decide_handle_raw_key)

    def _decide_handle_raw_key(self, vkCode, scanCode, extended, pressed):
        self.timer_manager.handle_input()
        return True

    @script(description=_("Open main window"))
    def script_show_dialog(self, gesture):
        MainDialog.show_main_dialog(self.timer_manager)

    @script(
        description=_(
            "Get information about next nearest timer, press twice to restart / disable"
        )
    )
    def script_get_next_timer_info(self, gesture):
        if getLastScriptRepeatCount() > 0 and self._last_nearest_timer is not None:
            self.do_action_with_nearest_timer()
            return
        timer_counter = 0
        nearest_timer = None
        nearest_important_timer_found = False
        for timer in self.timer_manager.enabled_timers:
            if not nearest_important_timer_found:
                if timer.waiting_for_user_action or timer.recurrent_notification_active:
                    nearest_timer = timer
                    nearest_important_timer_found = True
                elif (
                    nearest_timer is None
                    or timer.config.finish_time < nearest_timer.config.finish_time
                ):
                    nearest_timer = timer
            timer_counter += 1
            if nearest_important_timer_found and timer_counter > 1:
                break
        if nearest_timer is None:
            message(_("No timers found."))
            return
        components = []
        if nearest_timer.waiting_for_user_action:
            components.append(_("pending"))
        if nearest_timer.recurrent_notification_active:
            components.append(_("notifying recurrently"))
        if nearest_timer.config.state is TimerState.ACTIVE:
            duration = format_time(int(nearest_timer.config.finish_time - time.time()))
            components.append(_(f"{duration} left").format(duration=duration))
        if timer_counter > 1:
            components.append(nearest_timer.config.name)
        message(", ".join(components))
        self._last_nearest_timer = nearest_timer

    def do_action_with_nearest_timer(self):
        timer = self._last_nearest_timer
        components = []
        if timer.waiting_for_user_action:
            timer.start_next_round()
            next_round_component = [_("Next round started")]
            if timer.config.repeat_limit > 0:
                repeat_count_info = (
                    f"{timer.config.repeat_count} / {timer.config.repeat_limit}"
                )
                next_round_component.append(f"({repeat_count_info})")
            components.append(" ".join(next_round_component))
        elif timer.recurrent_notification_active:
            timer.stop_recurrent_notification()
            components.append(_("Recurrent notification stopped"))
        else:
            timer.disable()
            components.append(_("Disabled"))
        components.append(timer.config.name)
        self.timer_manager.update_timer(timer)
        message(", ".join(components))
        self._last_nearest_timer = None

    @script(description=_("Add timer"))
    def script_add_timer(self, event):
        show_dialog(NewTimerDialog, gui.mainFrame, self.timer_manager)
