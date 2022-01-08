# swayblur

<div align="center">
  <img src="https://github.com/WillPower3309/swayblur/blob/main/image.jpg?raw=true" />
</div>

> Basic i3ipc based script to blur an output's wallpaper when a client is present in it.
> Available via [pypi](https://pypi.org/project/swayblur/) or the [NUR](https://nur.nix-community.org/repos/willpower3309/).

## Installation

### Stable Release

Swayblur is available in the [NUR](https://nur.nix-community.org/repos/willpower3309/) or from [pypi](https://pypi.org/project/swayblur/):
```sh
pip install --user swayblur
```

### Building from Source

```sh
git clone https://github.com/willpower3309/swayblur
cd swayblur
pip install --user .
```

### Dependencies
+ `python-i3ipc`: build dependency for communicating with Sway
+ `ImageMagick`: used to generate the blurred wallpaper
+ `oguri`: used to set the wallpaper [without displaying a gray screen for a split second](https://github.com/swaywm/sway/issues/3693)

## Usage
**In order for the script to run as expected, your sway config should not set any wallpaper. Remove the `output * bg PATH` line.**

**swayblur does not spawn oguri at launch. If spawning swayblur with a sway config via `exec`, ensure that `exec oguri` occurs before swayblur is executed!

`swayblur [-h] [-b BLUR] [-a ANIMATE] [-c CONFIG-PATH] [-v VERBOSE]`

| Option | Description |
| ------ | ----------- |
| `-b`, `--blur`        | blur strength (default: 20, min: 5, max: 100)                |
| `-a`, `--animate`     | animation duration (default: 1, min: 1, max: 20)             |
| `-c`, `--config-path` | oguri config path (default: $XDG\_CONFIG\_HOME/oguri/config) |
| `-v`, `--verbose`     | prints additional information                                |
| `-h`, `--help`        | show the help message and exit                               |

## Configuration
Since swayblur requires `oguri`, it reads its config file: `~/.config/oguri/config`. I personally use the below config, it's about as minimal as you can get:

```
[output *]
image=PATH_TO_YOUR_WALLPAPER
filter=nearest
scaling-mode=fill
anchor=center
```
