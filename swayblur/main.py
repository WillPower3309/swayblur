import subprocess
import argparse
import pathlib
import i3ipc


BLUR_MIN = 5
BLUR_MAX = 100

CACHE_DIR = pathlib.Path.home() / '.cache/swayblur'


def framePath(frame: int) -> str:
    return '%s/%d.png' % (CACHE_DIR, frame)


class blurWallpaper:
    def __init__(self, wallpaperPath: str, blurStrength: int, animationDuration: int) -> None:
        self.SWAY = i3ipc.Connection()
        self.outputStatus = {}
        self.wallpaperPath = wallpaperPath
        self.blurFrames = [(i + 1) * (blurStrength // animationDuration) for i in range(animationDuration)]

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
        # TODO: threading
        index = 1
        for frame in self.blurFrames:
            if not pathlib.Path(framePath(frame)).is_file():
                print('Generating blurred wallpaper frame %d...' % index)
                subprocess.run([
                    'convert', self.wallpaperPath, '-blur', '0x%d' % frame, framePath(frame)
                ])
                index += 1
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
            for frame in reversed(self.blurFrames):
                self.switchWallpaper(focusedOutput, framePath(frame))
            self.switchWallpaper(focusedOutput, self.wallpaperPath)
            self.outputStatus[focusedOutput] = False

        elif not self.isWorkspaceEmpty() and not self.outputStatus[focusedOutput]:
            # set wallpaper to blurred
            for frame in self.blurFrames:
                self.switchWallpaper(focusedOutput, framePath(frame))
            self.outputStatus[focusedOutput] = True


    def switchWallpaper(self, output: str, path: str) -> None:
        subprocess.run(['ogurictl', 'output', output, '--image', path])



def main() -> None:
    # create the cache dir if it doesn't exist
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('wallpaper_path', type=str)
    parser.add_argument('-b', '--blur', type=int, default=20,
            help='the blur strength (default: %(default)d, min: {}, max: {})'.format(BLUR_MIN, BLUR_MAX))
    parser.add_argument('-a', '--animate', type=int, default=1,
            help='animation duration (default: %(default)d)')
    args = parser.parse_args()

    # Validate args
    if not pathlib.Path(args.wallpaper_path).is_file():
        print('Unable to run swayblur, no such file "%s"' % args.wallpaper_path)
        return
    if args.blur < BLUR_MIN or args.blur > BLUR_MAX:
        print('Unable to run swayblur, blur is set to %d, which is not between 10-100' % args.blur)
        return
    if args.animate < 1:
        print('Unable to run swayblur, animate is set to %d, which is not a positive value' % args.animate)
        return

    # Run blurring script
    blurWallpaper(args.wallpaper_path, args.blur, args.animate)



if __name__ == "__main__":
    main()

