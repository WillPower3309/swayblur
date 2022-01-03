import pathlib
import shutil

DEFAULT_OGURI_DIR = pathlib.Path.home() / '.config/oguri/config'

CACHE_DIR = pathlib.Path.home() / '.cache/swayblur'
CACHE_VALIDATION_FILE = CACHE_DIR / 'settings.json'

# create the cache dir if it doesn't exist
def createCache() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

# delete the cache dir
def deleteCache() -> None:
    shutil.rmtree(CACHE_DIR, ignore_errors=True)

# check if a path exists
def exists(path: str) -> bool:
    return pathlib.Path(path).is_file()

# returns the path to a given frame for a given output
def framePath(hash: str, frame: int) -> str:
    return '%s/%s-%d.png' % (CACHE_DIR, hash, frame)

# returns the path to a cached image based on its path + hash
def cachedImagePath(path: str, hash: str) -> str:
    return CACHE_DIR / ('%s%s' % (hash, pathlib.Path(path).suffix))
