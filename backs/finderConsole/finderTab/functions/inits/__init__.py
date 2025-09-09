# finderTab.__init__ additions
from PyQt6.QtCore import QTimer
import logging, os

# ... after building self.log QTextEdit ...
self._log_emitter = QtLogEmitter()
self._qt_handler = QtLogHandler(self._log_emitter)
self._qt_handler.setFormatter(CompactFormatter("%(asctime)s [%(levelname)s] %(message)s"))
logging.getLogger().addHandler(self._qt_handler)
self._log_emitter.new_log.connect(self.append_log)  # you already have append_log()

# Optional: tail the rotating file so external logs appear too
from main import get_log_file_path  # the getter we added in main.py
self._log_file = get_log_file_path()
self._tail_pos = 0

def _poll_logfile():
    try:
        with open(self._log_file, "r", encoding="utf-8", errors="replace") as f:
            f.seek(self._tail_pos)
            chunk = f.read()
            self._tail_pos = f.tell()
        if chunk:
            self.append_log(chunk)
    except FileNotFoundError:
        pass

self._tail_timer = QTimer(self)
self._tail_timer.setInterval(500)  # ms
self._tail_timer.timeout.connect(_poll_logfile)
self._tail_timer.start()
