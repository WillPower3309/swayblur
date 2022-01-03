import multiprocessing
import subprocess
import json
import filecmp
import shutil
import hashlib
import i3ipc

import paths
from output import Output


def genBlurredImage(inputPath: str, outputPath: str, blurLevel: int) -> None:
    try:
        subprocess.run(['convert', inputPath, '-blur', '0x%d' % blurLevel, outputPath])
    except FileNotFoundError:
        print('Could not create blurred version of wallpaper, ensure imagemagick is installed')
        exit()

    print('Generated image %s' % outputPath)


def verifySettingsCache(blurStrength: int, animationDuration: int) -> None:
    try:
        with open(paths.CACHE_VALIDATION_FILE, 'r') as f:
            settings = json.load(f)
            if settings['blur'] == blurStrength and settings['animate'] == animationDuration:
                return
    except FileNotFoundError:
        pass

    # new settings, clear & recreate cache
    paths.deleteCache()
    paths.createCache()

    with open(paths.CACHE_VALIDATION_FILE, 'w') as f:
        f.write(json.dumps({
            'blur': blurStrength,
            'animate': animationDuration,
        }))
    return


def verifyWallpaperCache(wallpaperPath: str, wallpaperHash: str) -> bool:
    cachedWallpaper = paths.cachedImagePath(wallpaperPath, wallpaperHash)

    if paths.exists(cachedWallpaper) and filecmp.cmp(wallpaperPath, cachedWallpaper):
        return True

    shutil.copy(wallpaperPath, cachedWallpaper)
    return False


class BlurManager:
    def __init__(self, outputConfigs: dict, blurStrength: int, animationDuration: int) -> None:
        self.SWAY = i3ipc.Connection()
        self.outputs = {}

        animationFrames = [
            (i + 1) * (blurStrength // animationDuration) for i in range(animationDuration)
        ]

        # clear cache if the blurStrength / animationDuration have been changed since last run
        verifySettingsCache(blurStrength, animationDuration)

        # create an output object for each output in the configuration
        for name in outputConfigs:
            outputCfg = outputConfigs[name]
            imageHash = hashlib.md5(outputCfg['image'].encode()).hexdigest()
            cachedImage = paths.cachedImagePath(outputCfg['image'], imageHash)

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
            if not verifyWallpaperCache(outputCfg['image'], imageHash):
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
        print("Listening...")
        self.SWAY.on(i3ipc.Event.WINDOW_NEW, self.handleBlur)
        self.SWAY.on(i3ipc.Event.WINDOW_CLOSE, self.handleBlur)
        self.SWAY.on(i3ipc.Event.WINDOW_MOVE, self.handleBlur)
        self.SWAY.on(i3ipc.Event.WORKSPACE_FOCUS, self.handleBlur)
        self.SWAY.main()


    def handleBlur(self, _sway: i3ipc.Connection, _event: i3ipc.Event) -> None:
        # get focused output
        # TODO: there's got to be a faster way to do this
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
