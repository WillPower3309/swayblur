# swayblur
Basic i3ipc based script to blur an output's wallpaper when a client is present in it.

## Requirements
+ `python-i3ipc`
+ `ImageMagick`: Used to generate the blurred wallpaper
+ `oguri`: used to set the wallpaper [without displaying a gray screen for a split second](https://github.com/swaywm/sway/issues/3693))

## TODO
[ ] Find a better way to handle multi monitor setups. As it currently stands, the script perfectly supports multi-monitor setups for all operations **except** when switching the first / last client from one monitor's focused workspace to another monitor's currently open but unfocused workspace.
