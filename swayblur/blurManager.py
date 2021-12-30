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


class BlurManager:
    def __init__(self, outputConfigs: dict, blurStrength: int, animationDuration: int) -> None:
        self.SWAY = i3ipc.Connection()
        self.outputs = {}

        animationFrames = [
            (i + 1) * (blurStrength // animationDuration) for i in range(animationDuration)
        ]

        for name in outputConfigs:
            outputCfg = outputConfigs[name]
            self.outputs[name] = Output(
                name,
                outputCfg['image'],
                [paths.framePath(name, frame) for frame in animationFrames],
                {
                    'filter': outputCfg['filter'] ,
                    'anchor': outputCfg['anchor'],
                    'scaling-mode': outputCfg['scaling-mode'],
                }
            )

        # TODO: add back cache validation, optimize me to not rely on output
        if True:
            print('Generating blurred wallpaper frames')
            print('This may take a minute...')
            for outputName in self.outputs:
                output = self.outputs[outputName]
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


    def handleBlur(self, _sway: i3ipc.Connection, _event: i3ipc.Event) -> None:
        # get focused output
        focusedOutput = ''
        for output in self.SWAY.get_outputs():
            if output.focused:
                focusedOutput = output.name
                break

        # check if the focused workspace is empty and blur or unblur accordingly
        focusedWindow = self.SWAY.get_tree().find_focused()
        if focusedWindow.name == focusedWindow.workspace().name: # if empty
            self.outputs[focusedOutput].blur()
        else:
            self.outputs[focusedOutput].unblur()
