#!/usr/bin/env bash
set -euo pipefail

root="/home/computron/Documents/pythonTools/modules/abstract_paths/src/abstract_paths/runner"

backup() { [ -f "$1" ] && cp -f "$1" "$1.bak" || true; }

# 1) Stop the accidental pause in the function exporter
f="$root/getFnames.py"; backup "$f"
python3 - <<'PY'
from pathlib import Path
p=Path("/home/computron/Documents/pythonTools/modules/abstract_paths/src/abstract_paths/runner/getFnames.py")
src=p.read_text()
src=src.replace("input(filepaths)","")  # remove blocking call
p.write_text(src)
print("patched getFnames.py")
PY

# 2) Make warning_utils Qt6-aware and import via our shared imports
f="$root/functions/warning_utils.py"; backup "$f"
cat > "$f" <<'PY'
from ...imports import *
import subprocess, traceback, os

def build_warnings_list(self):
    """
    QListWidget pre-wired with:
      • click  -> open + filtered log view
      • dblclick -> open only
    """
    lw = QListWidget()

    def _resolve(path: str) -> str:
        try:
            if self.cb_try_alt_ext.isChecked():
                return resolve_alt_ext(path, self.path_in.text().strip())
        except Exception:
            pass
        return path

    def _open_in_vscode(path: str, line: int, col: int | None):
        subprocess.run(["code", "-g", f"{path}:{line}:{(col or 1)}"], check=False)

    def on_click(item: QListWidgetItem):
        try:
            text = item.text()
            path, line, col = self._parse_item(text)
            path = _resolve(path)
            _open_in_vscode(path, line, col)
            snippet = self._extract_errors_for_file(
                self.last_output, path, self.path_in.text().strip()
            )
            self._replace_log(snippet if snippet else f"(No specific lines found for {path})\n\n{self.last_output}")
        except Exception:
            self.append_log("show_error_for_item error:\n" + traceback.format_exc() + "\n")

    def on_dblclick(item: QListWidgetItem):
        try:
            text = item.text()
            path, line, col = self._parse_item(text)
            path = _resolve(path)
            _open_in_vscode(path, line, col)
        except Exception:
            self.append_log("open_in_editor error:\n" + traceback.format_exc() + "\n")

    lw.itemClicked.connect(on_click)
    lw.itemDoubleClicked.connect(on_dblclick)
    return lw
PY

# 3) Ensure helper_utils provides create_radio_group and resolve_alt_ext
f="$root/functions/helper_utils.py"; backup "$f"
cat > "$f" <<'PY'
from ...imports import *
import os

# ── helpers ──────────────────────────────────────────────────────────────
def _replace_log(self, text: str):
    try:
        self.log_view.clear()
        self.log_view.insertPlainText(text)
    except Exception as e:
        print(f"{e}")

def _parse_item(self, info: str):
    try:
        parts = info.rsplit(":", 2)
        if len(parts) == 3:
            path, line, col = parts[0], parts[1], parts[2]
        else:
            path, line, col = parts[0], parts[1], "1"
        return path, int(line), int(col)
    except Exception as e:
        print(f"{e}")

def _extract_errors_for_file(self, combined_text: str, abs_path: str, project_root: str) -> str:
    try:
        text = combined_text or ""
        if not text:
            return ""
        try:
            rel = os.path.relpath(abs_path, project_root) if (project_root and abs_path.startswith(project_root)) else os.path.basename(abs_path)
        except Exception:
            rel = os.path.basename(abs_path)
        rel_alt = rel.replace("\\", "/")
        abs_alt = abs_path.replace("\\", "/")
        base = os.path.basename(abs_alt)
        lines = text.splitlines()
        blocks = []
        for i, ln in enumerate(lines):
            if (abs_alt in ln) or (rel_alt in ln) or (("src/" + base) in ln):
                start = max(0, i - 3)
                end = min(len(lines), i + 6)
                block = "\n".join(lines[start:end])
                blocks.append(f"\n— context @ log line {i+1} —\n{block}\n")
        return "\n".join(blocks).strip()
    except Exception as e:
        print(f"{e}")

def create_radio_group(self, labels, default_index=0, slot=None):
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

_PREFERRED_EXT_ORDER = [".tsx",".ts",".jsx",".js",".mjs",".cjs",".tsx",".ts",".jsx",".js",".css",".scss",".less"]
def resolve_alt_ext(path: str, project_root: str) -> str:
    """
    If 'path' doesn't exist, try swapping extensions using a common React stack order.
    Also try replacing absolute project-root prefix with relative 'src/' and vice-versa.
    """
    try_paths = [path]
    base, ext = os.path.splitext(path)
    for e in _PREFERRED_EXT_ORDER:
        try_paths.append(base + e)

    # also try joining with project_root, and under src/
    if project_root and not path.startswith(project_root):
        rel = path.lstrip("./")
        try_paths.extend([
            os.path.join(project_root, rel),
            os.path.join(project_root, "src", os.path.basename(base)) + ext,
        ])
        for e in _PREFERRED_EXT_ORDER:
            try_paths.append(os.path.join(project_root, "src", os.path.basename(base)) + e)

    for candidate in try_paths:
        if os.path.isfile(candidate):
            return candidate
    return path  # fallback
PY

# 4) Keep log + list utils (unchanged from your latest good version)
# Re-write logEntries_utils to import from shared and not rely on PyQt5 symbols
f="$root/functions/logEntries_utils.py"; backup "$f"
cat > "$f" <<'PY'
from ...imports import *

def append_log(self, text):
    cursor = self.log_view.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.End)
    self.log_view.setTextCursor(cursor)
    self.log_view.insertPlainText(text)

def set_last_output(self, text: str):
    self.last_output = text or ""
    self.apply_log_filter()

def show_error_entries(self, entries):
    self.errors_list.clear()
    self.append_log(f"[dbg] show_error_entries entries={len(entries)} widget_id={id(self.errors_list)}\n")
    if self.cb_try_alt_ext.isChecked():
        entries = [(resolve_alt_ext(p, self.path_in.text().strip()), ln, col) for (p, ln, col) in entries]
    if not entries:
        self.append_log("\n✅ No matching errors.\n")
        return
    self.append_log("\nErrors found:\n")
    for path, line, col in entries:
        info = f"{path}:{line}:{col or 1}"
        self.append_log(info + "\n")
        self.errors_list.addItem(QListWidgetItem(info))

def show_warning_entries(self, entries):
    self.warnings_list.clear()
    if self.cb_try_alt_ext.isChecked():
        entries = [(resolve_alt_ext(p, self.path_in.text().strip()), ln, col) for (p, ln, col) in entries]
    if not entries:
        self.append_log("\nℹ️ No warnings.\n")
        return
    self.append_log("\nWarnings found:\n")
    for path, line, col in entries:
        info = f"{path}:{line}:{col or 1}"
        self.append_log(info + "\n")
        self.warnings_list.addItem(QListWidgetItem(info))

def apply_log_filter(self):
    if self.rb_err.isChecked():
        self._replace_log(self.last_errors_only or "(no errors)")
    elif self.rb_wrn.isChecked():
        self._replace_log(self.last_warnings_only or "(no warnings)")
    else:
        self._replace_log(self.last_output or "")
PY

# 5) Make initializeInit rely on our helper create_radio_group (now present)
# (Your file already looks fine; leave as-is.)

# 6) Fix runner UI scaffolding: use runner_layout consistently; no undefined 'tabs'
f="$root/functions/runner.py"; backup "$f"
cat > "$f" <<'PY'
from ...imports import *

def getRunner(self, layout=None, tabs=None):
    """
    Build the Runner page into either:
      • provided 'tabs' (adds a tab), or
      • provided 'layout' (adds widgets), or
      • self (owns its own layout).
    """
    runner_page = QWidget()
    runner_layout = layout or QVBoxLayout(runner_page)

    # Top rows
    top = QHBoxLayout()
    top.addWidget(QLabel("User:"))
    top.addWidget(self.user_in, 2)
    top.addWidget(QLabel("Path:"))
    top.addWidget(self.path_in, 3)
    top.addWidget(self.run_btn)
    top.addWidget(self.rerun_btn)
    top.addWidget(self.clear_btn)
    runner_layout.addLayout(top)

    # Filter row
    filter_row = QHBoxLayout()
    filter_row.addWidget(QLabel("Log Output:"))
    filter_row.addStretch(1)
    filter_row.addWidget(self.rb_all)
    filter_row.addWidget(self.rb_err)
    filter_row.addWidget(self.rb_wrn)
    filter_row.addWidget(self.cb_try_alt_ext)
    runner_layout.addLayout(filter_row)

    runner_layout.addWidget(self.log_view, 3)

    left  = getListBox((self.errors_list,   "Errors (file:line:col):", 1))
    right = getListBox((self.warnings_list, "Warnings (file:line:col):", 1))
    lists_row = getRow(left, right)
    runner_layout.addLayout(lists_row, 2)

    # Add to tabs if provided
    if tabs is not None:
        tabs.addTab(runner_page, "Runner")
        return runner_page

    # Otherwise attach to self
    if layout is None:
        root_layout = QVBoxLayout(self)
        root_layout.addLayout(runner_layout)
    return runner_page
PY

# 7) Make main widget minimal (construct, init, build)
f="$root/main.py"; backup "$f"
cat > "$f" <<'PY'
from abstract_gui.QT6 import QWidget, QVBoxLayout, QTabWidget
from .initFuncs import initFuncs

class Runner(QWidget):
    def __init__(self, layout=None):
        super().__init__()
        # wire all functions first
        initFuncs(self)
        # set up state and widgets
        self.initializeInit()
        # build UI
        root = layout or QVBoxLayout(self)
        self.tabs = QTabWidget(self)
        root.addWidget(self.tabs)
        # build runner tab
        self.getRunner(tabs=self.tabs)

Runner = initFuncs(Runner)
PY

# 8) Ensure imports module exposes all Qt6 names used by helpers
f="$root/imports.py"; backup "$f"
cat > "$f" <<'PY'
from abstract_gui.QT6 import *
# Ensure these are present (depending on your re-exports)
# If abstract_gui.QT6 doesn't expose them, import from PyQt6 directly:
try:
    QTextCursor  # type: ignore
except NameError:
    from PyQt6.QtGui import QTextCursor
try:
    QProcess  # type: ignore
except NameError:
    from PyQt6.QtCore import QProcess
PY

# 9) Regenerate function exports (run your generator)
python3 "$root/getFnames.py" || true

echo "Patch complete."
