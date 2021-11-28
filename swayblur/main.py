import argparse
import pathlib
import filecmp
import shutil
import json
import multiprocessing
import subprocess
import configparser
import i3ipc


BLUR_MIN = 5
BLUR_MAX = 100
ANIMATE_MIN = 1
ANIMATE_MAX = 20

CACHE_DIR = pathlib.Path.home() / '.cache/swayblur'

def parseArgs() -> bool:
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--blur', type=int, default=20,
            help='The blur strength (default: %(default)d, min: {}, max: {})'.format(BLUR_MIN, BLUR_MAX))
    parser.add_argument('-a', '--animate', type=int, default=1,
            help='Animation duration (default: %(default)d, min: {}, max: {})'.format(ANIMATE_MIN, ANIMATE_MAX))
    parser.add_argument('-c', '--config-path', type=str, default=pathlib.Path.home() / '.config/oguri/config',
            help='Path to the oguri configuration file to use (default: %(default)s)')
    args = parser.parse_args()

    # Validate args
    if args.blur < BLUR_MIN or args.blur > BLUR_MAX:
        parser.error('Unable to run swayblur, blur is set to %d, which is not between %d-%d' % (args.blur, BLUR_MIN, BLUR_MAX))
    if args.animate < ANIMATE_MIN or args.animate > ANIMATE_MAX:
        parser.error('Unable to run swayblur, animate is set to %d, which is not between %d-%d' % (args.animate, ANIMATE_MIN, ANIMATE_MAX))
    if args.animate > args.blur:
        parser.error('Unable to run swayblur, animate value %d is greater than blur value %d' % (args.animate, args.blur))

    return args


def framePath(output: str, frame: int) -> str:
    return '%s/%s-%d.png' % (CACHE_DIR, output, frame)


def genFrame(wallpaperPath: str, output: str, frame: int) -> None:
    try:
        subprocess.run(['convert', wallpaperPath, '-blur', '0x%d' % frame, framePath(output, frame)])
    except FileNotFoundError:
        print('Could not create blurred version of wallpaper, ensure imagemagick is installed')
        exit()

    print('Generated frame %s' % framePath(output, frame))


class blurWallpaper:
    def __init__(self, configPath: str, blurStrength: int, animationDuration: int, cached: bool) -> None:
        self.SWAY = i3ipc.Connection()
        self.outputs = self.initOutputs(configPath)
        # TODO: self.focusedOutput
        self.blurFrames = [(i + 1) * (blurStrength // animationDuration) for i in range(animationDuration)]

        if not cached:
            self.genTransitionFrames()

        self.handleBlur(self.SWAY, i3ipc.Event.WORKSPACE_INIT)

        print("Listening...")
        self.SWAY.on(i3ipc.Event.WINDOW_NEW, self.handleBlur)
        self.SWAY.on(i3ipc.Event.WINDOW_CLOSE, self.handleBlur)
        self.SWAY.on(i3ipc.Event.WINDOW_MOVE, self.handleBlur)
        self.SWAY.on(i3ipc.Event.WORKSPACE_FOCUS, self.handleBlur)
        self.SWAY.main()


    def initOutputs(self, configPath: str) -> None:
    # TODO: add file not exist check
        config = configparser.ConfigParser()
        config.read(configPath)

        # init outputs to their defaults
        outputs = {}
        for output in i3ipc.Connection().get_outputs():
            outputs[output.name] = {
                'image': '',
                'filter': '',
                'anchor': '',
                'scaling-mode': 'fill',
                'is-blurred': False
            }

        # iterate through each output in the config
        # TODO: this could probably be faster
        for section in config.sections():
            outputName = section.split('output ')[-1]
            outputsToUpdate = []

            if outputName == '*':
                for output in outputs:
                    if outputs[output]['image'] == '':
                        outputsToUpdate.append(output)
            else:
                outputsToUpdate.append(outputName)

            for output in outputsToUpdate:
                for key in config[section]:
                    outputs[output][key] = config[section][key]

        return outputs


    def genTransitionFrames(self) -> None:
        print('Generating blurred wallpaper frames')
        print('This may take a minute...')
        for output in self.outputs:
            with multiprocessing.Pool() as pool:
                pool.starmap(genFrame, [[self.outputs[output]['image'], output, frame] for frame in self.blurFrames])
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

        if self.isWorkspaceEmpty() and self.outputs[focusedOutput]['is-blurred']:
            # set wallpaper to original
            for frame in reversed(self.blurFrames):
                self.switchWallpaper(focusedOutput, framePath(focusedOutput, frame))
            self.switchWallpaper(focusedOutput, self.outputs[focusedOutput]['image'])
            self.outputs[focusedOutput]['is-blurred'] = False

        elif not self.isWorkspaceEmpty() and not self.outputs[focusedOutput]['is-blurred']:
            # set wallpaper to blurred
            for frame in self.blurFrames:
                self.switchWallpaper(focusedOutput, framePath(focusedOutput, frame))
            self.outputs[focusedOutput]['is-blurred'] = True


    def switchWallpaper(self, outputName: str, path: str) -> None:
        output = self.outputs[outputName]

        try:
            subprocess.run([
                'ogurictl',
                'output', outputName,
                '--image', path,
                '--filter', output['filter'],
                '--anchor', output['anchor'],
                '--scaling-mode', output['scaling-mode']
            ])
        except:
            print('Could not set wallpaper, ensure oguri is installed')
            exit()


def main() -> None:
    # Parse arguments
    args = parseArgs()

    # Run blurring script
    blurWallpaper(args.config_path, args.blur, args.animate, False)


if __name__ == "__main__":
    main()

