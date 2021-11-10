import subprocess
import argparse
import pathlib
import i3ipc


BLUR_MIN = 5
BLUR_MAX = 100
CACHE_DIR = pathlib.Path.home() / '.cache/swayblur'


class blurWallpaper:
    def __init__(self, wallpaperPath: str, blurStrength: int) -> None:
        self.SWAY = i3ipc.Connection()
        self.outputStatus = {}
        self.wallpaperPath = wallpaperPath
        self.blurredWallpaperPath = '%s/%dblurredWallpaper.png' % (CACHE_DIR, blurStrength)

        self.genBlurredWallpaper(blurStrength)
        self.initOutputs()

        print("Listening...")
        self.SWAY.on(i3ipc.Event.WINDOW_NEW, self.handleBlur)
        self.SWAY.on(i3ipc.Event.WINDOW_CLOSE, self.handleBlur)
        self.SWAY.on(i3ipc.Event.WINDOW_MOVE, self.handleBlur)
        self.SWAY.on(i3ipc.Event.WORKSPACE_FOCUS, self.handleBlur)
        self.SWAY.main()


    def initOutputs(self) -> None:
        self.outputStatus = {}
        outputs = self.SWAY.get_outputs()
        for output in outputs:
            self.outputStatus[output.name] = False


    def genBlurredWallpaper(self, blurStrength: int) -> None:
        # TODO: better check
        if not pathlib.Path(self.blurredWallpaperPath).is_file():
            print('Generating blurred wallpaper...')
            subprocess.run(['convert', self.wallpaperPath, '-blur', '0x%d' % blurStrength, self.blurredWallpaperPath])
            print('Blurred wallpaper generated')


    def isWorkspaceEmpty(self) -> None:
        focused = self.SWAY.get_tree().find_focused()
        return focused.name == focused.workspace().name


    def handleBlur(self, _: i3ipc.Connection, event: i3ipc.Event) -> None:
        focusedOutput = ''

        for output in self.SWAY.get_outputs():
            if output.focused:
                focusedOutput = output.name
                break

        if self.isWorkspaceEmpty() and self.outputStatus[focusedOutput]:
            # set wallpaper to original
            self.switchWallpaper(focusedOutput, self.wallpaperPath)
            self.outputStatus[focusedOutput] = False

        elif not self.isWorkspaceEmpty() and not self.outputStatus[focusedOutput]:
            # set wallpaper to blurred
            self.switchWallpaper(focusedOutput, self.blurredWallpaperPath)
            self.outputStatus[focusedOutput] = True


    def switchWallpaper(self, output, path) -> None:
        subprocess.run(['ogurictl', 'output', output, '--image', path])



def main() -> None:
    # create the cache dir if it doesn't exist
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('wallpaper_path', type=str)
    parser.add_argument('-b', '--blur', type=int, default=20,
            help='the blur strength (default: %(default)d, min: {}, max: {})'.format(BLUR_MIN, BLUR_MAX))
    args = parser.parse_args()

    # Validate args
    if not pathlib.Path(args.wallpaper_path).is_file():
        print('Unable to run swayblur, no such file "%s"' % args.wallpaper_path)
        return
    if args.blur < BLUR_MIN or args.blur > BLUR_MAX:
        print('Unable to run swayblur, blur is set to %d, which is not between 10-100' % args.blur)
        return

    # Run blurring script
    blurWallpaper(args.wallpaper_path, args.blur)



if __name__ == "__main__":
    main()

