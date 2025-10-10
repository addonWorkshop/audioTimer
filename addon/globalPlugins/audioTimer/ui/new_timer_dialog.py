import wx
from gui.guiHelper import BoxSizerHelper

from ..enums import NotificationType, RestartPolicy, TimerFinishAction
from ..schema import TimerSchema
from ..timer_manager import TimerManager

MINUTE = 60
HOUR = MINUTE * 60

MAX_SIZE = 2**31 - 1


class NewTimerDialog(wx.Dialog):
    def __init__(self, parent, timer_manager: TimerManager):
        super().__init__(parent, title=_("New Timer"))
        self.timer_manager = timer_manager
        self.main_sizer = BoxSizerHelper(self, wx.VERTICAL)
        self.hours_field = self.main_sizer.addLabeledControl(
            _("Hours"), wx.SpinCtrl, min=0, max=MAX_SIZE
        )
        self.minutes_field = self.main_sizer.addLabeledControl(
            _("Minutes"), wx.SpinCtrl, min=0, max=59
        )
        self.seconds_field = self.main_sizer.addLabeledControl(
            _("Seconds"), wx.SpinCtrl, min=0, max=59
        )
        self.repeat_limit_field = self.main_sizer.addLabeledControl(
            _("Repeat limit (0 unlimited)"), wx.SpinCtrl, min=0, max=MAX_SIZE
        )
        self.repeat_limit_field.Bind(wx.EVT_SPINCTRL, self.on_repeat_limit_changed)
        self.notification_type_choice = self.main_sizer.addLabeledControl(
            _("Notify"), wx.Choice
        )
        self.notification_type_choice.Append(_("Once"), NotificationType.ONETIME)
        self.notification_type_choice.Append(
            _("Recurrently"), NotificationType.RECURRENT
        )
        self.notification_type_choice.SetSelection(0)
        self.notification_type_choice.Bind(
            wx.EVT_CHOICE, self.on_notification_type_changed
        )
        self.recurrent_notification_interval_field = self.main_sizer.addLabeledControl(
            _("Recurrent notification interval (in seconds)"), wx.SpinCtrl, min=1
        )
        self.restart_policy_choice = self.main_sizer.addLabeledControl(
            _("Restart"), wx.Choice
        )
        self.restart_policy_choice.Append(_("Immediately"), RestartPolicy.IMMEDIATE)
        self.restart_policy_choice.Append(_("Manually"), RestartPolicy.ON_USER_ACTION)
        self.restart_policy_choice.SetSelection(0)
        self.remove_after_last_repeat_cb = self.main_sizer.addLabeledControl(
            _("Remove after last repeat"), wx.CheckBox
        )
        self.remove_after_last_repeat_cb.SetValue(True)
        self.main_sizer.addDialogDismissButtons(wx.OK | wx.CANCEL, True)
        self.main_sizer.sizer.Fit(self)
        self.SetSizer(self.main_sizer.sizer)
        self.hours_field.SetFocus()
        self.Bind(wx.EVT_BUTTON, self.on_ok, id=wx.ID_OK)
        self.refresh()

    def refresh(self):
        (
            self.remove_after_last_repeat_cb.Hide()
            if self.repeat_limit_field.GetValue() == 0
            else self.remove_after_last_repeat_cb.Show()
        )
        notification_type = self.notification_type_choice.GetClientData(
            self.notification_type_choice.GetSelection()
        )
        (
            self.recurrent_notification_interval_field.Hide()
            if notification_type is not NotificationType.RECURRENT
            else self.recurrent_notification_interval_field.Show()
        )

    def on_repeat_limit_changed(self, event):
        self.refresh()

    def on_notification_type_changed(self, event):
        self.refresh()

    def on_ok(self, event):
        interval = (
            self.hours_field.GetValue() * HOUR
            + self.minutes_field.GetValue() * MINUTE
            + self.seconds_field.GetValue()
        )
        finish_action = (
            TimerFinishAction.REMOVE
            if self.remove_after_last_repeat_cb.GetValue()
            else TimerFinishAction.DISABLE
        )
        notification_type = self.notification_type_choice.GetClientData(
            self.notification_type_choice.GetSelection()
        )
        recurrent_notification_interval = (
            self.recurrent_notification_interval_field.GetValue()
            if notification_type == NotificationType.RECURRENT
            else 0
        )
        restart_policy = self.restart_policy_choice.GetClientData(
            self.restart_policy_choice.GetSelection()
        )
        new_timer = TimerSchema(
            name=self.timer_manager.generate_timer_name(),
            interval=interval,
            repeat_limit=self.repeat_limit_field.GetValue(),
            finish_action=finish_action,
            notification_type=notification_type,
            recurrent_notification_interval=recurrent_notification_interval,
            restart_policy=restart_policy,
        )
        self.timer_manager.add_timer(new_timer)
        event.Skip()
