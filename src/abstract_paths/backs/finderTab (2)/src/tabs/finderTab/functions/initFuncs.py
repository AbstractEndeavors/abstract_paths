

from abstract_utilities import get_logFile
from .functions import (append_log, initFuncs, populate_results, start_search, stop_search)
logger=get_logFile(__name__)
def initFuncs(self):
    try:
        for f in (append_log, initFuncs, populate_results, start_search, stop_search):
            setattr(self, f.__name__, f)
    except Exception as e:
        logger.info(f"{e}")
    return self
