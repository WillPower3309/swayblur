import subprocess

class Output:
    def __init__(self, name: str, wallpaper: str, blurFrames: list, settings: dict) -> None:
        self.name = name
        self.wallpaper = wallpaper
        self.blurFrames = blurFrames
        self.settings = settings
        self.isBlurred = False

    def blur(self) -> None:
        if not self.isBlurred:
            for framePath in self.blurFrames:
                self.switchWallpaper(framePath)
            self.isBlurred = True

    def unblur(self) -> None:
        if self.isBlurred:
            for framePath in reversed(self.blurFrames[:-1]):
                self.switchWallpaper(framePath)
            self.switchWallpaper(self.wallpaper)
            self.isBlurred = False

    def switchWallpaper(self, path: str) -> None:
        try:
            subprocess.run([
                'ogurictl',
                'output', self.name,
                '--image', path,
                '--filter', self.settings['filter'],
                '--anchor', self.settings['anchor'],
                '--scaling-mode', self.settings['scaling-mode']
            ])
        except:
            print('Could not set wallpaper, ensure oguri is installed')
            exit()
