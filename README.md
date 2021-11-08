# sway-blur
Basic i3ipc based script to blur an output's wallpaper when a client is present in it.

## Requirements
+ `python-i3ipc`
+ [`oguri`](https://github.com/vilhalmer/oguri)

Oguri is needed as the sway wallpaper has an [issue with displaying a gray screen for a split second before the wallpaper is changed](https://github.com/swaywm/sway/issues/3693).

## TODO
[ ] Find a better way to handle multi monitor setups. As it currently stands, the script perfectly supports multi-monitor setups for all operations **except** when switching the first / last client from one monitor's focused workspace to another monitor's currently open but unfocused workspace.
