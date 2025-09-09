from ...imports import *
def _start_func_scan(self, scope: str):
        path = self.path_in.text().strip()
        if not path or not os.path.isdir(path):
            QMessageBox.critical(self, "Error", "Invalid project path.")
            return
        self.func_console.appendLog(f"[map] starting scan ({scope})\n")

        entries = ["index", "main"]
        self.map_worker = ImportGraphWorker(path, scope=scope, entries=entries)
        self.map_worker.log.connect(self.func_console.appendLog)
        self.map_worker.ready.connect(self._on_map_ready)
        self.map_worker.finished.connect(lambda: self.func_console.appendLog("[map] done.\n"))
        self.map_worker.start()

def _on_map_ready(self, graph: dict, func_map: dict):
        self.graph = graph or {}
        self.func_map = func_map or {}
        self.func_console.setData(self.func_map)
def create_radio_group(self, labels, default_index=0, slot=None):
        """
        Create a QButtonGroup with QRadioButtons for the given labels.

        Args:
            self: parent widget (e.g. 'self' inside a class)
            labels (list[str]): button labels
            default_index (int): which button to check by default
            slot (callable): function to connect all toggled signals to
        Returns:
            (QButtonGroup, list[QRadioButton])
        """
        group = QButtonGroup(self)
        buttons = []

        for i, label in enumerate(labels):
            rb = QRadioButton(label)
            if i == default_index:
                rb.setChecked(True)
            group.addButton(rb)
            buttons.append(rb)
            if slot:
                rb.toggled.connect(slot)

        return group, buttons

