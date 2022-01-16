import multiprocessing
import subprocess
import filecmp
import shutil
import hashlib
import logging
import i3ipc

from swayblur import paths
from swayblur.output import Output

def genBlurredImage(inputPath: str, outputPath: str, blurLevel: int) -> None:
    try:
        subprocess.run(['convert', inputPath, '-blur', '0x%d' % blurLevel, outputPath])
    except FileNotFoundError:
        logging.error('Could not create blurred version of wallpaper, ensure imagemagick is installed')
        exit()

    logging.info('Generated image %s' % outputPath)


def verifyWallpaperCache(wallpaperPath: str, wallpaperHash: str) -> bool:
    cachedWallpaper = paths.cachedImagePath(wallpaperPath, wallpaperHash)

    if paths.exists(cachedWallpaper) and filecmp.cmp(wallpaperPath, cachedWallpaper):
        logging.info('wallpaper %s is cached as %s' % (wallpaperPath, cachedWallpaper))
        return True

    logging.info('wallpaper %s added to the cache as %s' % (wallpaperPath, cachedWallpaper))
    shutil.copy(wallpaperPath, cachedWallpaper)
    return False


class BlurManager:
    def __init__(self, outputConfigs: dict, blurStrength: int, animationDuration: int) -> None:
        self.SWAY = i3ipc.Connection()
        self.outputs = {}

        animationFrames = [
            (i + 1) * (blurStrength // animationDuration) for i in range(animationDuration)
        ]

        # create an output object for each output in the configuration
        for name in outputConfigs:
            outputCfg = outputConfigs[name]
            outputWallpaper = outputCfg['image']

            if not outputWallpaper: # if output has no wallpaper
                self.outputs[name] = Output(name, '', [], {})
                continue

            imageHash = hashlib.md5(outputWallpaper.encode()).hexdigest()
            cachedImage = paths.cachedImagePath(outputWallpaper, imageHash)

            self.outputs[name] = Output(
                name,
                cachedImage,
                [paths.framePath(imageHash, frame) for frame in animationFrames],
                {
                    'filter': outputCfg['filter'] ,
                    'anchor': outputCfg['anchor'],
                    'scaling-mode': outputCfg['scaling-mode'],
                }
            )

            # check if new wallpaper must be generated
            if not verifyWallpaperCache(outputWallpaper, imageHash):
                print('Generating blurred wallpaper frames')
                print('This may take a minute...')
                with multiprocessing.Pool() as pool:
                    pool.starmap(
                        genBlurredImage,
                        [[cachedImage, paths.framePath(imageHash, frame), frame] for frame in animationFrames]
                    )
                print('Blurred wallpaper generated for %s' % name)
            else:
                print('Blurred wallpaper exists for %s' % name)


    def start(self) -> None:
        # initially blur populated workspaces
        for workspace in self.SWAY.get_workspaces():
            if workspace.visible and workspace.ipc_data['focus']:
                    self.outputs[workspace.ipc_data['output']].blur()

        print("Listening...")
        self.SWAY.on(i3ipc.Event.WINDOW_MOVE, self.handleMove)
        self.SWAY.on(i3ipc.Event.WINDOW_NEW, self.handleNew)
        self.SWAY.on(i3ipc.Event.WINDOW_CLOSE, self.handleClose)
        self.SWAY.on(i3ipc.Event.WORKSPACE_FOCUS, self.handleFocus)
        self.SWAY.main()


    def handleMove(self, _: i3ipc.Connection, event: i3ipc.Event) -> None:
        container = self.SWAY.get_tree().find_by_id(event.ipc_data['container']['id'])
        containerOutput = ''
        focusedContainer = self.SWAY.get_tree().find_focused()
        focusedOutput = focusedContainer.workspace().ipc_data['output']

        try:
            containerOutput = container.workspace().ipc_data['output']
        except KeyError: # case when moved to scratchpad, deal with focused output
            if focusedContainer == focusedContainer.workspace(): # if workspace empty
                self.outputs[focusedOutput].unblur()
            return
        except AttributeError: # case where a previously scratchpadded window is closed
            # it doesn't make sense that closing a previously scratchpadded window
            # would be a WINDOW_MOVE event to me either, but it is what it is
            return

        # window moved to a workspace on a different output
        if container != focusedContainer:
            self.outputs[containerOutput].blur()
            if focusedContainer == focusedContainer.workspace(): # if workspace empty
                self.outputs[focusedOutput].unblur()
        # window moved to a new workspace on same output
        elif container == container.workspace(): # if workspace is empty
            self.outputs[containerOutput].unblur()


    def handleNew(self, _: i3ipc.Connection, event: i3ipc.Event) -> None:
        container = self.SWAY.get_tree().find_by_id(event.ipc_data['container']['id'])
        workspace = container.workspace()

        self.outputs[workspace.ipc_data['output']].blur()


    def handleClose(self, _: i3ipc.Connection, _event: i3ipc.Event) -> None:
        container = self.SWAY.get_tree().find_focused()
        workspace = container.workspace()

        if container == workspace: # if workspace is empty
            self.outputs[workspace.ipc_data['output']].unblur()


    def handleFocus(self, _: i3ipc.Connection, _event: i3ipc.Event) -> None:
        container = self.SWAY.get_tree().find_focused()
        workspace = container.workspace()

        if container == workspace: # if workspace is empty
            self.outputs[workspace.ipc_data['output']].unblur()
        else:
            self.outputs[workspace.ipc_data['output']].blur()
