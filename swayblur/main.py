import argparse
import pathlib
import filecmp
import shutil
import json
import multiprocessing
import subprocess
import i3ipc


BLUR_MIN = 5
BLUR_MAX = 100
ANIMATE_MIN = 1
ANIMATE_MAX = 20

CACHE_DIR = pathlib.Path.home() / '.cache/swayblur'


def parseArgs() -> bool:
    parser = argparse.ArgumentParser()
    parser.add_argument('wallpaper_path', type=str)
    parser.add_argument('-b', '--blur', type=int, default=20,
            help='the blur strength (default: %(default)d, min: {}, max: {})'.format(BLUR_MIN, BLUR_MAX))
    parser.add_argument('-a', '--animate', type=int, default=1,
            help='animation duration (default: %(default)d, min: {}, max: {})'.format(ANIMATE_MIN, ANIMATE_MAX))
    args = parser.parse_args()

    # Validate args
    if not pathlib.Path(args.wallpaper_path).is_file():
        parser.error('Unable to run swayblur, no such file "%s"' % args.wallpaper_path)
    if args.blur < BLUR_MIN or args.blur > BLUR_MAX:
        parser.error('Unable to run swayblur, blur is set to %d, which is not between %d-%d' % (args.blur, BLUR_MIN, BLUR_MAX))
    if args.animate < ANIMATE_MIN or args.animate > ANIMATE_MAX:
        parser.error('Unable to run swayblur, animate is set to %d, which is not between %d-%d' % (args.animate, ANIMATE_MIN, ANIMATE_MAX))
    if args.animate > args.blur:
        parser.error('Unable to run swayblur, animate value %d is greater than blur value %d' % (args.animate, args.blur))

    return args


def validateCache(wallpaperPath: str, blurStrength: int, animationDuration: int) -> bool:
    SETTINGS_FILE = CACHE_DIR / 'settings.json'

    try:
        with open(SETTINGS_FILE, 'r') as f:
            settings = json.load(f)
            if settings['blur'] == blurStrength and settings['animate'] == animationDuration and filecmp.cmp(settings['referenceFile'], wallpaperPath):
                return True
    except FileNotFoundError:
        print('Creating cache directory: %s' % CACHE_DIR)
        pass

    shutil.rmtree(CACHE_DIR, ignore_errors=True)
    CACHE_DIR.mkdir(parents=True)
    referenceFile = shutil.copy(wallpaperPath, CACHE_DIR)
    with open(SETTINGS_FILE, 'w') as f:
        f.write(json.dumps({
            'referenceFile': referenceFile,
            'blur': blurStrength,
            'animate': animationDuration,
        }))
    return False

def framePath(frame: int) -> str:
    return '%s/%d.png' % (CACHE_DIR, frame)


def genFrame(wallpaperPath: str, frame: int) -> None:
    try:
        subprocess.run(['convert', wallpaperPath, '-blur', '0x%d' % frame, framePath(frame)])
    except FileNotFoundError:
        print('Could not create blurred version of wallpaper, ensure imagemagick is installed')
        exit()

    print('Generated frame %d' % frame)


class blurWallpaper:
    def __init__(self, wallpaperPath: str, blurStrength: int, animationDuration: int, cached: bool) -> None:
        self.SWAY = i3ipc.Connection()
        self.outputStatus = {}
        self.wallpaperPath = wallpaperPath
        self.blurFrames = [(i + 1) * (blurStrength // animationDuration) for i in range(animationDuration)]

        if not cached:
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
        try:
            subprocess.run(['ogurictl', 'output', output, '--image', path])
        except:
            print('Could not set wallpaper, ensure oguri is installed')
            exit()


def main() -> None:
    # Parse arguments
    args = parseArgs()

    # Validate cache
    isCached = validateCache(args.wallpaper_path, args.blur, args.animate)

    # Run blurring script
    blurWallpaper(args.wallpaper_path, args.blur, args.animate, isCached)


if __name__ == "__main__":
    main()

