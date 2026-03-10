from ...imports import *
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

class diffParserTab(QWidget):
    def __init__(self, bus: SharedStateBus):
        super().__init__()

        root = QVBoxLayout(self)

        # Common inputs (dir, filters, etc.)
        grid = QGridLayout()
        install_common_inputs(
            self, grid, bus=bus,
            default_dir_in=os.getcwd(),
            primary_btn=("Preview", self.preview_patch),
            secondary_btn=("Save", self.save_patch),
            trinary_btn=("Save All", (lambda: self.save_all_checked())),
            default_allowed_exts_in=False,
            default_exclude_dirs_in=True
        )

        # Files tree (match results)
        root.addWidget(QLabel("Files found:"))
        self.files_list = QTreeWidget()
        self.files_list.setColumnCount(3)
        self.files_list.setHeaderLabels(["File", "Apply", "Overwrite"])
        self.files_list.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.files_list.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.files_list.header().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.files_list.setRootIsDecorated(False)
        # handlers
        self.files_list.itemDoubleClicked.connect(self._open_file_from_row)
        self.files_list.currentItemChanged.connect(lambda *_: self._on_tree_selection_changed())
        root.addWidget(self.files_list, stretch=1)

        # Diff / Preview split
        self.splitter = QSplitter(Qt.Orientation.Horizontal, self)

        left = QWidget(); lv = QVBoxLayout(left); lv.setContentsMargins(0,0,0,0)
        lv.addWidget(QLabel("Diff:"))
        self.diff_text = QTextEdit()
        self.diff_text.setPlaceholderText("Paste the diff here...")
        lv.addWidget(self.diff_text, stretch=1)

        right = QWidget(); rv = QVBoxLayout(right); rv.setContentsMargins(0,0,0,0)
        rv.addWidget(QLabel("Preview:"))
        self.preview = QTextEdit(); self.preview.setReadOnly(True)
        rv.addWidget(self.preview, stretch=1)

        self.splitter.addWidget(left)
        self.splitter.addWidget(right)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 1)
        root.addWidget(self.splitter, stretch=3)

        # Actions
##        btn_preview = QPushButton("Parse and Preview")
##        btn_preview.clicked.connect(self.preview_patch)
##        root.addWidget(btn_preview)
##
##        btn_save = QPushButton("Approve and Save")
##        btn_save.clicked.connect(self.save_patch)
##        root.addWidget(btn_save)
##        
##        self.saveAllBtn = QPushButton("Approve and Save All")
##        self.saveAllBtn.clicked.connect(lambda: self.save_all_checked()) 
##        root.addWidget(self.saveAllBtn)
        
        # Status line
        self.status_label = QLabel("Ready.")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.status_label.setStyleSheet("color: #4caf50; padding: 4px 0;")
        root.addWidget(self.status_label)

get_init_funcs(diffParserTab,get_caller_dir())
