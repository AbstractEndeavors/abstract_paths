#!/usr/bin/env python3
import sys, os
from PyQt6.QtWidgets import QApplication
from main import finderConsole
from abstract_gui.QT6.utils.console_utils.start_console import startConsole
from abstract_gui.QT6.utils.shared_bus import SharedStateBus
from abstract_paths import reset_find_console_stop

def main():
    # determine target directory
    directory = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    os.environ.setdefault("QT_QPA_PLATFORM", "xcb")
    os.environ.setdefault("QT_STYLE_OVERRIDE", "Fusion")

    # create the shared bus and console
    reset_find_console_stop()
    bus = SharedStateBus()

    # construct a closure that injects directory into every tab
    def console_factory():
        win = finderConsole(bus=bus)
        # propagate the starting directory into tabs that have dir_in
        for i in range(win.layout().count()):
            widget = win.layout().itemAt(i).widget()
            if hasattr(widget, "dir_in"):
                widget.dir_in.setText(directory)
        win.setWindowTitle(f"Abstract Finder Console — {directory}")
        return win

    # launch via your universal console runner (handles logging/resizing)
    startConsole(console_factory)

if __name__ == "__main__":
    main()
