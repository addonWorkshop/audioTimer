import wx

_dialogs = {}


def show_dialog(dialog_class, *args, _scheduled=False, **kwargs):
    if not _scheduled:
        wx.CallAfter(show_dialog, dialog_class, *args, _scheduled=True, **kwargs)
        return
    dialog = _dialogs.get(dialog_class, None)
    if dialog is not None:
        dialog.Raise()
        return
    try:
        with dialog_class(*args, **kwargs) as dialog:
            _dialogs[dialog_class] = dialog
            dialog.Raise()
            dialog.ShowModal()
    finally:
        _dialogs.pop(dialog_class)
