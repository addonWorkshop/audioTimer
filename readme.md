# Audio Timer

This NVDA add-on provides a flexible timer system that can be useful for a wide variety of tasks, from cooking and exercises to managing work intervals with the Pomodoro technique.

## Features

- Multiple timers, each with its own unique settings.
- Custom timer names (partly implemented).
- Repeats: configure the number of times a timer should repeat. It can run once or repeat for a specified count.
- Recurrent notifications: When the timer has finished, notifications will play repeatedly at the configured interval until you turn them off.
- Manual restart: timer could be configured to restart immediately or manually.
- Custom notification sounds for every timer (not implemented).

## Usage
Go to nvda -> Preferences -> Input gestures and configure gesture for opening audio timer dialog.

Here you also can configure the following gesture: Get information about next nearest timer, press twice to restart / disable.

This feature will be called quick action gesture for short in this readme, it was described below in detail.

Press configured hotkey to open main window, here you can add new timers or interact with existing.

Press add button to open New Timer dialog, here timer round duration, amount of repeats and other settings could be configured.

To add the timer, press OK button or press enter on any field  in the dialog.

To manage existing timer, select it in the timers list, press applications key or shift+f10 and choose appropriate option.

### Quick action
You could interact with the nearest timer without opening the dialog using quick action.

Pressing assigned hotkey once will report the current state of the timer.

When pressed twice, it will change timer state according to the current timer state.

1. If the timer is pending (manual restart configured), next round will be started.
2. If recurrent notification is active, it will be stopped.
3. Otherwise, timer will be disabled.

## Change log
### 0.9.0
Added ability to add new timer by gesture directly (as in 0.7).

### 0.8
Addon rewritten and reworked.

Current Second script (ctrl+nvda+f12) was removed, it was added to the [Dev Box](https://github.com/addonWorkshop/devBox) nvda addon.

### 0.7

Added translation and documentation.
