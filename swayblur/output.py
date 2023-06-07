import subprocess
import logging

class Output:
    def __init__(self, name: str, wallpaper: str, blurFrames: list, settings: dict) -> None:
        self.name = name
        self.wallpaper = wallpaper
        self.blurFrames = blurFrames
        self.isBlurred = False

        settings.pop('image')
        self.opts = [elt for item in settings.items() for elt in item if elt is not None]

    def blur(self) -> None:
        if not self.isBlurred:
            for framePath in self.blurFrames:
                self.switchWallpaper(framePath)
            self.isBlurred = True

    def unblur(self) -> None:
        if self.isBlurred:
            for framePath in self.blurFrames[:0:-1]:
                self.switchWallpaper(framePath)
            self.switchWallpaper(self.wallpaper)
            self.isBlurred = False

    def switchWallpaper(self, path: str) -> None:
        if self.wallpaper: # not all outputs have wallpaper
            try:
                subprocess.run([
                    'swww', 'img',
                    '--outputs', self.name,
                    *self.opts,
                    path
                ])
                logging.info('Changed output %s wallpaper to %s' % (self.name, path))
            except:
                logging.error('Could not set wallpaper, ensure swww is installed')
                exit()
