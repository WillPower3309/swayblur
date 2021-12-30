import argparse

import paths
from blurManager import BlurManager


BLUR_MIN = 5
BLUR_MAX = 100
ANIMATE_MIN = 1
ANIMATE_MAX = 20


# parse and validate the arguments
def parseArgs() -> bool:
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--blur', type=int, default=20,
            help='The blur strength (default: %(default)d, min: {}, max: {})'.format(BLUR_MIN, BLUR_MAX))
    parser.add_argument('-a', '--animate', type=int, default=1,
            help='Animation duration (default: %(default)d, min: {}, max: {})'.format(ANIMATE_MIN, ANIMATE_MAX))
    parser.add_argument('-c', '--config-path', type=str, default=paths.DEFAULT_OGURI_DIR,
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


def main() -> None:
    # parse arguments
    args = parseArgs()

    # create the cache dir if it doesn't exist
    paths.createCache()

    # blur the wallpaper
    blurManager = BlurManager(args.config_path, args.blur, args.animate)
    blurManager.start()


if __name__ == "__main__":
    main()
