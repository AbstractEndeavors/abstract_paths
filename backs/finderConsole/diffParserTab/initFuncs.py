

from abstract_utilities import get_logFile
from .functions import (browse_file, preview_patch, save_patch)
logger=get_logFile(__name__)
def initFuncs(self):
    try:
        for f in (browse_file, preview_patch, save_patch):
            setattr(self, f.__name__, f)
    except Exception as e:
        logger.info(f"{e}")
    return self
