#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-.}"

# 1) Imports PyQt5 -> PyQt6 (Core/Widgets) and ensure QTextCursor import
grep -rl --include='*.py' -e 'from PyQt5.QtCore import' "$ROOT" | xargs -r sed -i 's/from PyQt5\.QtCore import/from PyQt6.QtCore import/g'
grep -rl --include='*.py' -e 'from PyQt5.QtWidgets import' "$ROOT" | xargs -r sed -i 's/from PyQt5\.QtWidgets import/from PyQt6.QtWidgets import/g'

# Ensure PyQt6.QtGui QTextCursor is imported if a file uses QTextEdit or append_log
# Add import line if missing and file references QTextEdit or QTextCursor usage
while IFS= read -r -d '' f; do
  if grep -qE 'QTextEdit|QTextCursor|moveCursor\(' "$f"; then
    if ! grep -q 'from PyQt6.QtGui import QTextCursor' "$f"; then
      # Insert after first block of Qt imports
      awk '
        BEGIN{added=0}
        {
          print $0
          if (!added && $0 ~ /^from PyQt6\.QtWidgets import|^from PyQt6\.QtCore import/) {
            # Peek next line to avoid duplicating on multiple import blocks
          }
        }
      ' "$f" > "$f.tmp"

      # Simpler, robust insertion: add if not present anywhere
      echo 'from PyQt6.QtGui import QTextCursor' >> "$f"
    fi
  fi
done < <(find "$ROOT" -type f -name '*.py' -print0)

# 2) QTextEdit.NoWrap -> LineWrapMode.NoWrap
grep -rl --include='*.py' -e 'QTextEdit.NoWrap' "$ROOT" | xargs -r sed -i 's/QTextEdit\.NoWrap/QTextEdit.LineWrapMode.NoWrap/g'

# 3) app.exec_() -> app.exec()
grep -rl --include='*.py' -e 'exec_()' "$ROOT" | xargs -r sed -i 's/exec_()/exec()/g'

# 4) log.moveCursor(self.log.textCursor().End) -> QTextCursor.MoveOperation.End
# covers both "self.log" or other widgets; be a bit generic
grep -rl --include='*.py' -e '\.moveCursor(.*textCursor\(\)\.End' "$ROOT" | \
  xargs -r sed -i 's/\.moveCursor(.*textCursor\(\)\.End)/.moveCursor(QTextCursor.MoveOperation.End)/g'

# 5) (Optional) QSizePolicy / Alignment fixes if present in these files
grep -rl --include='*.py' -e 'QSizePolicy\.Expanding' "$ROOT" | xargs -r sed -i 's/QSizePolicy\.Expanding/QSizePolicy.Policy.Expanding/g'
grep -rl --include='*.py' -e 'Qt\.Align' "$ROOT" | xargs -r sed -i 's/Qt\.Align/Qt.AlignmentFlag.Align/g'

echo "✅ Qt6 patch completed for: $ROOT"
