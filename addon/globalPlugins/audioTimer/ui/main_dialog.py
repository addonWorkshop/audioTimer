import time

import gui
import wx
from gui.guiHelper import BoxSizerHelper

from ..enums import RestartPolicy, TimerState
from ..timer import Timer
from ..timer_manager import TimerManager
from ..utils import format_time
from .new_timer_dialog import NewTimerDialog
from .timer_menu import TimerMenu


class MainDialog(wx.Dialog):
    _dialog = None

    def __init__(self, timer_manager: TimerManager):
        super().__init__(parent=gui.mainFrame, title="Audio Timer", style=wx.CLOSE_BOX)
        self.timer_manager = timer_manager
        self.main_sizer = BoxSizerHelper(self, wx.VERTICAL)
        self.timer_list = self.main_sizer.addLabeledControl(
            _("Timers"),
            wx.ListCtrl,
            style=wx.LC_REPORT | wx.LC_NO_HEADER | wx.LC_SINGLE_SEL,
        )
        self.timer_list.AppendColumn("Timer")
        self.timer_list.Bind(wx.EVT_CONTEXT_MENU, self.on_context_menu)
        self.button_sizer = BoxSizerHelper(self, wx.HORIZONTAL)
        self.add_btn = self.button_sizer.addItem(wx.Button(self, label=_("Add")))
        self.add_btn.Bind(wx.EVT_BUTTON, self.on_add_btn)
        self.main_sizer.addItem(self.button_sizer)
        self.close_btn = self.button_sizer.addItem(
            wx.Button(self, id=wx.ID_CLOSE, label=_("Close"))
        )
        self.close_btn.Bind(wx.EVT_BUTTON, self.on_close_btn)
        self.main_sizer.sizer.Fit(self)
        self.SetSizer(self.main_sizer.sizer)
        self.SetEscapeId(wx.ID_CLOSE)
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.refresh_timer_list(True)
        self.timer_manager.register_update_callback(self.on_timers_update)

    @classmethod
    def show_main_dialog(cls, timer_manager):
        if cls._dialog is None:
            cls._dialog = MainDialog(timer_manager)
            cls._dialog.Show()
        gui.mainFrame.Raise()
        cls._dialog.SetFocus()

    @classmethod
    def _clear_main_dialog(cls):
        cls._dialog = None

    def on_close_btn(self, event):
        self.Close()

    def on_close(self, event):
        self._clear_main_dialog()
        self.timer_manager.unregister_update_callback(self.on_timers_update)
        self.Destroy()

    def on_timers_update(self):
        if wx.IsMainThread():
            # This check is needed because this method can be indirectly called from
            # the main (ui) thread,and from the manager thread.
            self.refresh_timer_list()
        else:
            wx.CallAfter(self.refresh_timer_list)

    def _get_timer_label(self, timer: Timer):
        # TODO: add comments for translators.
        components = [timer.config.name]
        if not timer.enabled:
            components.append(_("disabled"))
            return ", ".join(components)
        repeat_limit_component = None
        if timer.config.repeat_limit > 0:
            repeat_limit_component = (
                f"({timer.config.repeat_count} / {timer.config.repeat_limit})"
            )
        if timer.config.state is TimerState.ACTIVE:
            time_left = format_time(int(timer.config.finish_time - time.time()))
            active_components = [
                _("{time_left} left").format(time_left=time_left),
                *([] if repeat_limit_component is None else [repeat_limit_component]),
            ]
            components.append(" ".join(active_components))
        else:  # Pending
            if (
                timer.config.restart_policy is RestartPolicy.ON_USER_ACTION
                and not timer.repeat_limit_reached
            ):
                pending_components = [
                    _("pending"),
                    *(
                        []
                        if repeat_limit_component is None
                        else [repeat_limit_component]
                    ),
                ]
                components.append(" ".join(pending_components))
        if timer.recurrent_notification_active:
            components.append(_("notifying recurrently"))
        return ", ".join(components)

    def refresh_timer_list(self, select_first=False):
        initial_item_count = self.timer_list.GetItemCount()
        selected_index = self.timer_list.GetFirstSelected()
        selected_timer_id = None
        if selected_index > -1:
            selected_timer_id = self.timer_list.GetItemData(selected_index)
        current_timers: dict[int, int] = {}
        for i in range(self.timer_list.GetItemCount()):
            timer_id = self.timer_list.GetItemData(i)
            current_timers[timer_id] = i
        manager_timers: dict[int, tuple[int, Timer]] = {
            timer.config.id: (i, timer)
            for i, timer in enumerate(self.timer_manager.timers)
        }
        # Delete timers that no longer exist in the manager.
        # Indexes in the current_timers are ordered in ascending order,
        # So simply reverse and pop from highest to lowest.
        for timer_id, i in list(current_timers.items())[::-1]:
            if timer_id not in manager_timers:
                self.timer_list.DeleteItem(i)
                current_timers.pop(timer_id)
        # Now timer list in the ui is a subset of manager_timers.
        for timer_id, (manager_timer_index, timer) in manager_timers.items():
            ui_index = current_timers.get(timer_id, None)
            if ui_index is None:
                # New timer
                self.timer_list.InsertItem(
                    manager_timer_index, self._get_timer_label(timer)
                )
                self.timer_list.SetItemData(manager_timer_index, timer_id)
            else:
                # Existing timer, set new text for it in any case,
                # and update actual id if order is changed.
                self.timer_list.SetItemText(
                    manager_timer_index, self._get_timer_label(timer)
                )
                if manager_timer_index != ui_index:
                    self.timer_list.SetItemData(manager_timer_index, timer_id)
            current_timers[timer_id] = manager_timer_index
        # It seems that Select and Focus not raises exception,
        # so potential out of bounds is not a problem.
        if select_first or (
            initial_item_count == 0 and self.timer_list.GetItemCount() > 0
        ):
            self.timer_list.Focus(0)
            self.timer_list.Select(0)
            return
        if selected_index < 0:
            # Nothing was selected before, no need to reselect.
            return
        if selected_timer_id not in current_timers:
            # Previously selected timer was removed, so select the nearest.
            new_selection_index = min(
                selected_index, self.timer_list.GetItemCount() - 1
            )
        else:
            new_selection_index = current_timers[selected_timer_id]
        self.timer_list.Select(new_selection_index)
        self.timer_list.Focus(new_selection_index)

    def on_context_menu(self, event):
        first_selected_index = self.timer_list.GetFirstSelected()
        if first_selected_index < 0:
            return
        if event.GetPosition() == wx.DefaultPosition:
            # Applications key
            position = self.timer_list.GetItemRect(first_selected_index).GetBottomLeft()
        else:
            # Mouse right click
            position = wx.DefaultPosition
        timer_id = self.timer_list.GetItemData(first_selected_index)
        timer = self.timer_manager.get_timer(timer_id)
        menu = TimerMenu(self.timer_manager, timer)
        menu.popup_timer_menu(self.timer_list, position)

    def on_add_btn(self, event):
        with NewTimerDialog(self, self.timer_manager) as new_timer_dialog:
            new_timer_dialog.ShowModal()
