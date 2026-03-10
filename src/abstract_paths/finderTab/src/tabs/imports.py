from ..imports import *
from abstract_utilities import *
def get_all_imports(directory=None, sysroot=None, globs=None, target=None, include_private=True):
    """
    Import all .py files under `directory`.

    - if target is None → populate globals (old behavior)
    - if target is a class instance → attach attributes directly to it
    """
    directory = directory or get_initial_caller_dir()
    globs = globs or get_true_globals() or globals()

    files = collect_globs(directory=directory, allowed_exts='.py').get("files")
    sysroot = sysroot or switch_to_monorepo_root(directory=directory, files=files)

    for glo in files:
        imp = get_import_with_sysroot(glo, sysroot)
        module = importlib.import_module(imp)

        names = [
            n for n in dir(module)
            if not n.startswith("__") and (include_private or not n.startswith("_"))
        ]

        if target is None:
            # old behavior: inject into globals
            for name in names:
                globs[name] = getattr(module, name)
        else:
            # NEW behavior: bind directly to class instance
            for name in names:
                setattr(target, name, getattr(module, name))

    return target or globs

def get_init_funcs(self,abs_dir):
    abs_dir = get_caller_dir()
    dirlist = os.listdir(abs_dir)
    [get_all_imports(target=self,directory=os.path.join(abs_dir,key),include_private=True) for key in ['functions','functions.py'] if key in dirlist]
