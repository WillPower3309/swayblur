# swayblur

<div align="center">
  <img src="https://github.com/WillPower3309/swayblur/blob/main/image.jpg?raw=true" />
</div>

> Basic i3ipc based script to blur an output's wallpaper when a client is present in it.
> Available via [pypi](https://pypi.org/project/swayblur/), the [AUR](https://aur.archlinux.org/packages/swayblur/), or the [NUR](https://nur.nix-community.org/repos/willpower3309/).

## Installation

### Stable Release

Swayblur is available in the [AUR](https://aur.archlinux.org/packages/swayblur/), [NUR](https://nur.nix-community.org/repos/willpower3309/) or from [pypi](https://pypi.org/project/swayblur/):
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
+ `swww: used to set the wallpaper (https://github.com/WillPower3309/swayblur/issues/16)

## Usage
**In order for the script to run as expected, your sway config should not set any wallpaper. Remove the `output * bg PATH` line.**

**swayblur does not spawn swww at launch. If spawning swayblur with a sway config via `exec`, ensure that `exec swww init` occurs before swayblur is executed!**

`swayblur [-h] [-b BLUR] [-a ANIMATE] [-c CONFIG-PATH] [-v] [--verbose]`

| Option | Description |
| ------ | ----------- |
| `-b`, `--blur`        | blur strength (default: 20, min: 5, max: 100)                |
| `-a`, `--animate`     | animation duration (default: 1, min: 1, max: 20)             |
| `-c`, `--config-path` | config path (default: $XDG\_CONFIG\_HOME/swayblur/config) |
|       `--verbose`     | prints additional information                                |
| `-v`, `--version`     | show program's version number and exit                       |
| `-h`, `--help`        | show the help message and exit                               |

## Configuration
Swayblur reads a config file in `~/.config/swayblur/config`.

Each section title follows the name `[output <OUTPUT>]` and configures the
given output.

The output name `*` will match any output not specified elsewhere in the file. To find your output names, consult your compositor's manual.

The key `image` must be present and its value must be your wallpaper.

The other keys are all available options for `swww img`, with leading dashes, and
without value for flags without arguments.

I personally use the below config, it's about as minimal as you can get:

```
[output *]
image=PATH_TO_YOUR_WALLPAPER
--transition-step=255
```
