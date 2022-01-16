import argparse
import configparser
import json
import logging
import i3ipc

from swayblur.__about__ import __version__
from swayblur import paths
from swayblur.blurManager import BlurManager


# parse and validate the arguments
def parseArgs() -> bool:
    BLUR_MIN = 5
    BLUR_MAX = 100
    ANIMATE_MIN = 1
    ANIMATE_MAX = 20

    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--blur', type=int, default=20,
            help='The blur strength (default: %(default)d, min: {}, max: {})'.format(BLUR_MIN, BLUR_MAX))
    parser.add_argument('-a', '--animate', type=int, default=1,
            help='Animation duration (default: %(default)d, min: {}, max: {})'.format(ANIMATE_MIN, ANIMATE_MAX))
    parser.add_argument('-c', '--config-path', type=str, default=paths.DEFAULT_OGURI_DIR,
            help='Path to the oguri configuration file to use (default: %(default)s)')
    parser.add_argument('-v', '--version', action='version',
            version=f'%(prog)s {__version__}')
    parser.add_argument('--verbose', action='store_true',
            help='Prints additional information')
    args = parser.parse_args()

    # Validate args
    if args.blur < BLUR_MIN or args.blur > BLUR_MAX:
        parser.error('Unable to run swayblur, blur is set to %d, which is not between %d-%d' % (args.blur, BLUR_MIN, BLUR_MAX))
    if args.animate < ANIMATE_MIN or args.animate > ANIMATE_MAX:
        parser.error('Unable to run swayblur, animate is set to %d, which is not between %d-%d' % (args.animate, ANIMATE_MIN, ANIMATE_MAX))
    if args.animate > args.blur:
        parser.error('Unable to run swayblur, animate value %d is greater than blur value %d' % (args.animate, args.blur))
    if not paths.exists(args.config_path):
        parser.error('Unable to run swayblur, oguri config %s not found' % (args.config_path))

    return args


# parse the oguri config
def parseConfig(configPath: str) -> dict:
    config = configparser.ConfigParser()
    config.read(configPath)

    # init outputs to their defaults
    outputSettings = {}
    for output in i3ipc.Connection().get_outputs():
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


def verifySettingsCache(blurStrength: int, animationDuration: int) -> None:
    try:
        with open(paths.CACHE_VALIDATION_FILE, 'r') as f:
            settings = json.load(f)
            if settings['blur'] == blurStrength and settings['animate'] == animationDuration:
                return
    except FileNotFoundError:
        pass

    # new settings, clear & recreate cache
    logging.info('New swayblur settings found, recreating cache...')
    paths.deleteCache()
    paths.createCache()

    with open(paths.CACHE_VALIDATION_FILE, 'w') as f:
        f.write(json.dumps({
            'blur': blurStrength,
            'animate': animationDuration,
        }))
    return


def configureLogger() -> None:
    logging.basicConfig(format='[%(levelname)s\033[0m] %(message)s')
    logging.addLevelName(logging.INFO, '\033[1;34mI')
    logging.addLevelName(logging.ERROR, '\033[1;31mE')


def main() -> None:
    # parse arguments
    args = parseArgs()

    # setup logger
    configureLogger()
    if args.verbose:
        logging.getLogger().setLevel(logging.INFO)

    # parse oguri config
    outputConfigs = parseConfig(args.config_path)

    # clear cache if the blurStrength / animationDuration have been changed since last run
    verifySettingsCache(args.blur, args.animate)

    # blur the wallpaper
    blurManager = BlurManager(outputConfigs, args.blur, args.animate)
    blurManager.start()


if __name__ == "__main__":
    main()
