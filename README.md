# swayblur
Basic i3ipc based script to blur an output's wallpaper when a client is present in it.

## Requirements
+ `python-i3ipc`
+ `ImageMagick`: Used to generate the blurred wallpaper
+ `oguri`: used to set the wallpaper [without displaying a gray screen for a split second](https://github.com/swaywm/sway/issues/3693))

## Usage
`swayblur [-h] [-b BLUR] [-a ANIMATE] [-c CONFIG-PATH]`

| Option | Description |
| ------ | ----------- |
| `-b`, `--blur`        | blur strength (default: 20, min: 5, max: 100)                |
| `-a`, `--animate`     | animation duration (default: 1, min: 1, max: 20)             |
| `-c`, `--config-path` | oguri config path (default: $XDG\_CONFIG\_HOME/oguri/config) |
| `-h`, `--help`        | show the help message and exit                               |

**In order for the script to run as expected, your sway config should not set any wallpaper. Remove the `output * bg PATH` line.**

## Configuration
Since swayblur requires `oguri`, it reads its config file: `~/.config/oguri/config`. I personally use the below config, it's about as minimal as you can get:

```
[output *]
image=PATH_TO_YOUR_WALLPAPER
filter=nearest
scaling-mode=fill
anchor=center
```
