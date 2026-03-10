

from abstract_utilities import get_logFile
from .functions import (_build_import_index, _copy_imports, _fill_files, _fill_imports, _on_import_selection_changed, _open_selected_module_path, append_log, display_imports, start_extract)
logger=get_logFile(__name__)
def initFuncs(self):
    try:
        for f in (_build_import_index, _copy_imports, _fill_files, _fill_imports, _on_import_selection_changed, _open_selected_module_path, append_log, display_imports, start_extract):
            setattr(self, f.__name__, f)
    except Exception as e:
        logger.info(f"{e}")
    return self
