from ..imports import *
# — UI helpers —

# — Actions —
def start_search(self):
    self.list.clear()
    self.worker.log.clear()
    self.btn_run.setEnabled(False)
    try:
        params = self.make_params()
    except Exception as e:
        QMessageBox.critical(self, "Bad input", str(e))
        self.btn_run.setEnabled(True)
        return
    self.worker = SearchWorker(params)
    self.worker.log.connect(self.append_log)
    self.worker.done.connect(self.populate_results)
    self.worker.finished.connect(lambda: self.btn_run.setEnabled(True))
    self.worker.start()
def append_log(self, text: str):
    self.log.moveCursor(self.log.textCursor().MoveOperation.End)
    self.log.insertPlainText(text)
def populate_results(self, results: list):
    self._last_results = results or []
    if not results:
        self.append_log("✅ No matches found.\n")
        self.btn_secondary.setEnabled(False)
        return
    self.append_log(f"✅ Found {len(results)} file(s).\n")
    self.btn_secondary.setEnabled(True)
    for fp in results:
        if isinstance(fp, dict):
            file_path = fp.get("file_path")
            lines = fp.get("lines", [])
        else:
            file_path = fp
            lines = []
        if not isinstance(file_path, str):
            continue
        if lines:
            for obj in lines:
                line = obj.get('line')
                content = obj.get('content')
                text = f"{file_path}:{line}"
                self.list.addItem(QListWidgetItem(text))
                self.append_log(text + "\n")
        else:
            self.list.addItem(QListWidgetItem(file_path))
            self.append_log(file_path + "\n")
def open_one(self, item: QListWidgetItem):
    info = item.text()
    # VS Code: code -g file:line[:col]
    os.system(f'code -g "{info}"')
def open_all_hits(self):
    for i in range(self.list.count()):
        self.open_one(self.list.item(i))
