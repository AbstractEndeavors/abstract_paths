

from abstract_utilities import get_logFile
from .functions import (_ask_user_to_pick_file, apply_diff_to_directory, browse_dir, make_params, preview_patch, save_patch, set_status)
logger=get_logFile(__name__)
def initFuncs(self):
    try:
        for f in (_ask_user_to_pick_file, apply_diff_to_directory, browse_dir, make_params, preview_patch, save_patch, set_status):
            setattr(self, f.__name__, f)
    except Exception as e:
        logger.info(f"{e}")
    return self
