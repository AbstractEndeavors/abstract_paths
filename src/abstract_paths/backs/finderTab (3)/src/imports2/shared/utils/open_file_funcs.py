# open_file_funcs.py
from .imports import *
CONDA_PATH = "~/open_with_conda.sh"
def get_py_executable(path):
    try:
        if os.path.isfile(CONDA_PATH):
            return [CONDA_PATH,path]
        return [sys.executable,"-m", "idlelib",path]
    except Exception as e:
        logger.info(e) 
def _extract_path_line_from_item(item: QListWidgetItem) -> tuple[str, int | None]:
    try:
        data = item.data(Qt.ItemDataRole.UserRole)
        print(f"from _extract_path_line_from_item data == {data}")
        if isinstance(data, dict) and "file_path" in data:
            return data["file_path"], data.get("line")
        text = item.text()
        path, sep, rest = text.partition(":")
        line = int(rest.strip()) if sep and rest.strip().isdigit() else None
        return path, line
    except Exception as e:
        logger.info(e) 
def open_one(self, item: QListWidgetItem | None = None):
    try:
        print(f"from open_one item == {item}")
        # When called from code (no item), use current selection
        if item is None and hasattr(self, "list"):
            item = self.list.currentItem()

        if item is None:
            parent = self if isinstance(self, QWidget) else None
            QMessageBox.information(parent, "Open", "No item selected.")
            return

        path, line = _extract_path_line_from_item(item)
        open_in_editor(path, line)
    except Exception as e:
        logger.info(e) 
def open_all_hits(self):
    try:
        if not hasattr(self, "list"):
            return
        for i in range(self.list.count()):
            itm = self.list.item(i)
            path, line = _extract_path_line_from_item(itm)
            open_in_editor(path, line)
    except Exception as e:
        logger.info(e) 
# open_file_funcs.py
def open_in_editor(path: str, line: int | None = None):
   
        path = os.path.abspath(path)
        print(f"from open_in_editor path == {path}")
        if not os.path.exists(path):
            QMessageBox.warning(None, "Open File", f"File not found:\n{path}")
            return
        basename = os.path.basename(path)
        filename,ext = os.path.splitext(basename)
        print(f"from open_in_editor ext == {ext}")
        if ext == '.py':
            subprocess.Popen(get_py_executable(path))
            return


        # 2) VS Code first
        code = shutil.which("code")
        print(f"from open_in_editor code == {ext}")
        if code:
            target = f"{path}:{line or 1}"
            subprocess.Popen([code, "-g", target])
            return

