import argparse
import pathlib
import multiprocessing
import shutil
import subprocess
import i3ipc


BLUR_MIN = 5
BLUR_MAX = 100

ANIMATE_MIN = 1
ANIMATE_MAX = 20

CACHE_DIR = pathlib.Path.home() / '.cache/swayblur'


def invalidateCache(settingsHash: str):
    lockFile = CACHE_DIR / 'settings.lock'
    try:
        with open(lockFile, 'r') as f:
            if settingsHash == f.readline():
                return
    except FileNotFoundError:
        print('Created cache directory: %s' % CACHE_DIR)
        pass
    print('Settings updated')
    shutil.rmtree(CACHE_DIR, ignore_errors=True)
    CACHE_DIR.mkdir(parents=True)
    with open(lockFile, 'w') as f:
        f.write(settingsHash)


def framePath(frame: int) -> str:
    return '%s/%d.png' % (CACHE_DIR, frame)


def genFrame(wallpaperPath: str, frame: int) -> None:
    # TODO: better check
    if not pathlib.Path(framePath(frame)).is_file():
        subprocess.run([
            'convert', wallpaperPath, '-blur', '0x%d' % frame, framePath(frame)
        ])
        print('Generated frame %d' % frame)



class blurWallpaper:
    def __init__(self, wallpaperPath: str, blurStrength: int, animationDuration: int) -> None:
        self.SWAY = i3ipc.Connection()
        self.outputStatus = {}
        self.wallpaperPath = wallpaperPath
        self.blurFrames = [(i + 1) * (blurStrength // animationDuration) for i in range(animationDuration)]

        self.genTransitionFrames()
        self.initOutputs()

        self.handleBlur(self.SWAY, i3ipc.Event.WORKSPACE_INIT)

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


    def genTransitionFrames(self) -> None:
        print('Generating blurred wallpaper frames')
        print('This may take a minute...')
        with multiprocessing.Pool() as pool:
            pool.starmap(genFrame, [[self.wallpaperPath, frame] for frame in self.blurFrames])
        print('Blurred wallpaper generated')



    def isWorkspaceEmpty(self) -> None:
        focused = self.SWAY.get_tree().find_focused()
        return focused.name == focused.workspace().name


    def handleBlur(self, _sway: i3ipc.Connection, _event: i3ipc.Event) -> None:
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
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('wallpaper_path', type=str)
    parser.add_argument('-b', '--blur', type=int, default=20,
            help='the blur strength (default: %(default)d, min: {}, max: {})'.format(BLUR_MIN, BLUR_MAX))
    parser.add_argument('-a', '--animate', type=int, default=1,
            help='animation duration (default: %(default)d, min: {}, max: {})'.format(ANIMATE_MIN, ANIMATE_MAX))
    args = parser.parse_args()

    # Validate args
    if not pathlib.Path(args.wallpaper_path).is_file():
        print('Unable to run swayblur, no such file "%s"' % args.wallpaper_path)
        return
    if args.blur < BLUR_MIN or args.blur > BLUR_MAX:
        print('Unable to run swayblur, blur is set to %d, which is not between %d-%d' % (args.blur, BLUR_MIN, BLUR_MAX))
        return
    if args.animate < ANIMATE_MIN or args.animate > ANIMATE_MAX:
        print('Unable to run swayblur, animate is set to %d, which is not between %d-%d' % (args.animate, ANIMATE_MIN, ANIMATE_MAX))
        return
    if args.animate > args.blur:
        print('Unable to run swayblur, animate value %d is greater than blur value %d' % (args.animate, args.blur))
        return

    # Invalidate settings cache
    settingsHash = str(args.animate) + args.wallpaper_path + str(args.blur)
    invalidateCache(settingsHash)

    # Run blurring script
    blurWallpaper(args.wallpaper_path, args.blur, args.animate)



if __name__ == "__main__":
    main()

