import os
import i3ipc

WALLPAPER_PATH = '/home/will/wallpaper/wallpaper.jpg'
BLURRED_WALLPAPER_PATH = '/home/will/wallpaper/wallpaperBlurred.jpg'

class blurWallpaper:
    SWAY = i3ipc.Connection()
    outputStatus = {}

    def __init__(self):
        self.initOutputs()

        self.SWAY.on(i3ipc.Event.WINDOW_NEW, self.handleBlur)
        self.SWAY.on(i3ipc.Event.WINDOW_CLOSE, self.handleBlur)
        self.SWAY.on(i3ipc.Event.WINDOW_MOVE, self.handleBlur)
        self.SWAY.on(i3ipc.Event.WORKSPACE_FOCUS, self.handleBlur)
        self.SWAY.main()

    def initOutputs(self):
        self.outputStatus = {}
        outputs = self.SWAY.get_outputs()
        for output in outputs:
            self.outputStatus[output.name] = False

    def isWorkspaceEmpty(self):
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
            self.switchWallpaper(focusedOutput, WALLPAPER_PATH)
            self.outputStatus[focusedOutput] = False

        elif not self.isWorkspaceEmpty() and not self.outputStatus[focusedOutput]:
            # set wallpaper to blurred
            self.switchWallpaper(focusedOutput, BLURRED_WALLPAPER_PATH)
            self.outputStatus[focusedOutput] = True

    def switchWallpaper(self, output, path) -> None:
        os.system('ogurictl output %s --image %s' % (output, path));

blurWallpaper()
