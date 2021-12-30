import pathlib

DEFAULT_OGURI_DIR = pathlib.Path.home() / '.config/oguri/config'

CACHE_DIR = pathlib.Path.home() / '.cache/swayblur'

# create the cache dir if it doesn't exist
def createCache() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

# check if a path exists
def exists(path: str) -> bool:
    return pathlib.Path(path).is_file()

# returns the path to a given frame for a given output
def framePath(output: str, frame: int) -> str:
    return '%s/%s-%d.png' % (CACHE_DIR, output, frame)
