import sys

from .config import Settings
from .pipeline import run

if __name__ == "__main__":
    sys.exit(run(Settings.from_env()))
