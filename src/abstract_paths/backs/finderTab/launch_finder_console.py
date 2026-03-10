#!/usr/bin/env python3
import sys, os, json, time
from PyQt6.QtCore import QCoreApplication
from PyQt6.QtNetwork import QLocalServer, QLocalSocket
from .src import startFinderConsole

APP_KEY = "abstract_finder_console"

def send_to_existing_instance(target_dir: str) -> bool:
    """Try to send target_dir to an already running console."""
    sock = QLocalSocket()
    sock.connectToServer(APP_KEY)
    if not sock.waitForConnected(200):
        return False  # no instance
    payload = json.dumps({"dir": target_dir}).encode()
    sock.write(payload)
    sock.flush()
    sock.waitForBytesWritten(500)
    sock.disconnectFromServer()
    return True

def run_new_instance(target_dir: str):
    """Run Finder Console and listen for new directory requests."""
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(sys.argv)
    server = QLocalServer()

    # Remove stale socket
    if QLocalServer.removeServer(APP_KEY):
        time.sleep(0.05)
    if not server.listen(APP_KEY):
        # Try again if still blocked
        time.sleep(0.1)
        QLocalServer.removeServer(APP_KEY)
        server.listen(APP_KEY)

    win = startFinderConsole()

    # Wait a bit for GUI to initialize before accepting socket events
    app.processEvents()

    def on_new_connection():
        client = server.nextPendingConnection()
        if not client:
            return
        if client.waitForReadyRead(1000):
            try:
                data = bytes(client.readAll()).decode()
                msg = json.loads(data)
                new_dir = msg.get("dir")
                if new_dir and os.path.isdir(new_dir):
                    if hasattr(win, "dir_in"):
                        win.dir_in.setText(new_dir)
                        print(f"🔄 Updated directory → {new_dir}")
                    win.showNormal()
                    win.raise_()
                    win.activateWindow()
            except Exception as e:
                print("Error parsing socket data:", e)
        client.disconnectFromServer()

    server.newConnection.connect(on_new_connection)
    app.exec()

if __name__ == "__main__":
    target_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    if not os.path.isdir(target_dir):
        target_dir = os.path.dirname(target_dir)
    os.chdir(target_dir)

    # if an instance is already running, send it the new directory
    if send_to_existing_instance(target_dir):
        print(f"➡ Sent new directory to running instance: {target_dir}")
        sys.exit(0)

    # otherwise start the app fresh
    print(f"🧭 Starting new Finder Console instance at: {target_dir}")
    run_new_instance(target_dir)
