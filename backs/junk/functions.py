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
    # ── actions ──────────────────────────────────────────────────────────────
    def start_work(self):
        try:
            self.run_btn.setEnabled(False)
            user = self.user_in.text().strip() or 'solcatcher'   # <- swap order (yours hard-coded the default)
            path = self.path_in.text().strip()
            if not path or not os.path.isdir(path):
                QMessageBox.critical(self, "Error", "Invalid project path.")
                self.run_btn.setEnabled(True)
                return

            # Clear old UI bits
            self.errors_list.clear()
            self.warnings_list.clear()

            # Kick off non-blocking build
            self._run_build_qprocess(path)

        except Exception:
            self.append_log("start_work error:\n" + traceback.format_exc() + "\n")
            self.run_btn.setEnabled(True)

    def clear_ui(self):
        self.log_view.clear()
        self.errors_list.clear()
        self.warnings_list.clear()
        self.last_output = ""
        self.last_errors_only = ""
        self.last_warnings_only = ""

    # ── log + entries ────────────────────────────────────────────────────────
    def append_log(self, text):
        cursor = self.log_view.textCursor()
        cursor.movePosition(QTextCursor.End)
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

    # ── click handlers ───────────────────────────────────────────────────────
    def show_error_for_item(self, item: QListWidgetItem):
        info = item.text()
        try:
            path, line, col = self._parse_item(info)
            if self.cb_try_alt_ext.isChecked():
                path = resolve_alt_ext(path, self.path_in.text().strip())
            os.system(f'code -g "{path}:{line}:{col or 1}"')
            snippet = self._extract_errors_for_file(self.last_output, path, self.path_in.text().strip())
            self._replace_log(snippet if snippet else f"(No specific lines found for {path})\n\n{self.last_output}")
        except Exception:
            self.append_log("show_error_for_item error:\n" + traceback.format_exc() + "\n")

    def open_in_editor(self, item: QListWidgetItem):
        try:
            text = item.text()
            path, line, col = self._parse_item(text)
            if self.cb_try_alt_ext.isChecked():
                path = resolve_alt_ext(path, self.path_in.text().strip())
            os.system(f'code -g "{path}:{line}:{col or 1}"')
        except Exception:
            self.append_log("open_in_editor error:\n" + traceback.format_exc() + "\n")

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
        """
        Return only lines for the clicked file (with small context windows).
        Matches absolute path and likely relative forms (e.g., src/foo.tsx(...)).
        """
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
    def scan_functions(self):
        try:
            path = self.path_in.text().strip()
            if not path or not os.path.isdir(path):
                QMessageBox.critical(self, "Error", "Invalid project path.")
                return
            scope = self.scope_combo.currentText()
            self.btn_scan.setEnabled(False)
            self.append_log(f"[map] starting scan ({scope})\n")

            entries_txt = "index,main"  # or add a QLineEdit for this
            entries = [s.strip() for s in entries_txt.split(",") if s.strip()]
            self.map_worker = ImportGraphWorker(path, scope=scope, entries=entries)
            self.map_worker.log.connect(self.append_log)
            self.map_worker.ready.connect(self._on_map_ready)
            self.map_worker.finished.connect(lambda: self.btn_scan.setEnabled(True))
            self.map_worker.start()
        except Exception as e:
            print(f"{e}")

    def _on_map_ready(self, graph: dict, func_map: dict):
        self.graph = graph or {}
        self.func_map = func_map or {}
        self.func_console.setData(self.func_map)


    def _pick_build_cmd(self, project_dir: str):
        # choose yarn/pnpm/npm by lockfile
        if os.path.exists(os.path.join(project_dir, "yarn.lock")):
            return "yarn", ["build"]
        if os.path.exists(os.path.join(project_dir, "pnpm-lock.yaml")):
            return "pnpm", ["build"]
        return "npm", ["run", "build"]

    def _run_build_qprocess(self, project_dir: str):
        # Prefer QProcess so the GUI stays responsive
        self.proc = QProcess(self)
        self.proc.setWorkingDirectory(project_dir)
        self.proc.setProcessChannelMode(QProcess.MergedChannels)

        # If you use nvm, PATH may be missing node/yarn; run via bash -lc
        tool, args = self._pick_build_cmd(project_dir)
        sh = f'''
            set -e
            if [ -s "$HOME/.nvm/nvm.sh" ]; then . "$HOME/.nvm/nvm.sh"; fi
            if command -v corepack >/dev/null 2>&1; then corepack enable >/dev/null 2>&1 || true; fi
            {tool} --version >/dev/null 2>&1 || true
            {"yarn install --frozen-lockfile &&" if tool=="yarn" else ""}
            {"pnpm install --frozen-lockfile &&" if tool=="pnpm" else ""}
            {"npm ci &&" if tool=="npm" else ""}
            {tool} {" ".join(args)}
        '''.strip()

        self.proc.readyReadStandardOutput.connect(
            lambda: self.append_log(bytes(self.proc.readAllStandardOutput()).decode("utf-8", "ignore"))
        )
        self.proc.finished.connect(lambda code, status:
            self.append_log(f"\n\n[build] exited with code {code}\n") or self.run_btn.setEnabled(True)
        )
        self.proc.errorOccurred.connect(lambda err:
            self.append_log(f"\n[build] QProcess error: {err}\n") or self.run_btn.setEnabled(True)
        )

        # Start!
        self.run_btn.setEnabled(False)
        self.append_log(f"[build] cwd={project_dir}\n")
        self.proc.start("bash", ["-lc", sh])
