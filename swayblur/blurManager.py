import configparser
import multiprocessing
import subprocess
import i3ipc

import paths
from output import Output


def genFrame(wallpaperPath: str, output: str, frame: int) -> None:
    try:
        subprocess.run(['convert', wallpaperPath, '-blur', '0x%d' % frame, paths.framePath(output, frame)])
    except FileNotFoundError:
        print('Could not create blurred version of wallpaper, ensure imagemagick is installed')
        exit()

    print('Generated frame %s' % paths.framePath(output, frame))


# parse the oguri config
def parseConfig(outputs: list, configPath: str) -> dict:
    # check if config file exists
    if not paths.exists(configPath):
        print('Error: Oguri config file %s does not exist' % configPath)
        exit()

    config = configparser.ConfigParser()
    config.read(configPath)

    # init outputs to their defaults
    outputSettings = {}
    for output in outputs:
        outputSettings[output.name] = {
            'image': '',
            'filter': '',
            'anchor': '',
            'scaling-mode': 'fill',
            'is-blurred': False
        }

    # iterate through each output in the config
    for section in config.sections():
        outputName = section.split('output ')[-1]
        outputsToUpdate = []

        if outputName == '*':
            for output in outputSettings:
                if outputSettings[output]['image'] == '':
                    outputsToUpdate.append(output)
        else:
            outputsToUpdate.append(outputName)

        for output in outputsToUpdate:
            for key in config[section]:
                outputSettings[output][key] = config[section][key]

        return outputSettings


class BlurManager:
    def __init__(self, configPath: str, blurStrength: int, animationDuration: int) -> None:
        self.SWAY = i3ipc.Connection()
        self.outputsMap = {}
        self.outputs = []

        animationFrames = [
            (i + 1) * (blurStrength // animationDuration) for i in range(animationDuration)
        ]

        outputConfigs = parseConfig(self.SWAY.get_outputs(), configPath)
        i = 0
        for name in outputConfigs:
            outputCfg = outputConfigs[name]
            self.outputs.append(
                Output(
                    name,
                    outputCfg['image'],
                    [paths.framePath(name, frame) for frame in animationFrames],
                    {
                        'filter': outputCfg['filter'] ,
                        'anchor': outputCfg['anchor'],
                        'scaling-mode': outputCfg['scaling-mode'],
                    }
                )
            )
            self.outputsMap[name] = i
            i += 1

        # TODO: add back cache validation, optimize me to not rely on output
        if True:
            print('Generating blurred wallpaper frames')
            print('This may take a minute...')
            for output in self.outputs:
                with multiprocessing.Pool() as pool:
                    pool.starmap(genFrame, [[output.wallpaper, output.name, frame] for frame in animationFrames])
            print('Blurred wallpaper generated')


    def start(self) -> None:
        self.handleBlur(self.SWAY, i3ipc.Event.WORKSPACE_INIT)

        print("Listening...")
        self.SWAY.on(i3ipc.Event.WINDOW_NEW, self.handleBlur)
        self.SWAY.on(i3ipc.Event.WINDOW_CLOSE, self.handleBlur)
        self.SWAY.on(i3ipc.Event.WINDOW_MOVE, self.handleBlur)
        self.SWAY.on(i3ipc.Event.WORKSPACE_FOCUS, self.handleBlur)
        self.SWAY.main()


    def isWorkspaceEmpty(self) -> None:
        focused = self.SWAY.get_tree().find_focused()
        return focused.name == focused.workspace().name


    def getOutput(self, name: str) -> str:
        return self.outputs[self.outputsMap[name]]


    def handleBlur(self, _sway: i3ipc.Connection, _event: i3ipc.Event) -> None:
        # get focused output
        focusedOutput = ''
        for output in self.SWAY.get_outputs():
            if output.focused:
                focusedOutput = output.name
                break

        if self.isWorkspaceEmpty():
            self.getOutput(focusedOutput).blur()
        elif not self.isWorkspaceEmpty():
            self.getOutput(focusedOutput).unblur()
