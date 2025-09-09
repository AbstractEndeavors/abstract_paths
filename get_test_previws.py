from abstract_paths.content_utils.diff_engine import *
# abstract_ide/utils/managers/utils/mainWindow/functions/init_tabs/finder/DiffParserTab/diff_apply.py


import re


# ──────────────────────────────────────────────────────────────────────────────
# Diff parsing (simple unified-ish: leading '-' and '+'; blank/other delimits)
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class Hunk:
    
    subs: List[str] = field(default_factory=list)   # lines without leading '-'
    adds: List[str] = field(default_factory=list)   # lines without leading '+'

def parse_diff_text(diff_text: str) -> List[Hunk]:
    try:
        hunks: List[Hunk] = []
        cur = None
        open_block = False

        def close():
            nonlocal cur, open_block
            if open_block and cur and (cur.subs or cur.adds):
                hunks.append(cur)
            cur, open_block = None, False

        for raw in diff_text.split('\n'):
            if raw.startswith('-'):
                if not open_block:
                    cur = Hunk()
                    open_block = True
                cur.subs.append(raw[1:])
            elif raw.startswith('+'):
                if not open_block:
                    cur = Hunk()
                    open_block = True
                cur.adds.append(raw[1:])
            else:
                if open_block:
                    close()
        if open_block:
            close()
        return hunks
    except Exception as e:
        logger.info(f"parse_diff_text: {e}")
# ───────────────────────────
diff_text = """
-def browse_dir(self):
    d = QFileDialog.getExistingDirectory(self, "Choose directory", self.dir_in.text() or os.getcwd())
    if d:
        self.dir_in.setText(d)
+def browse_dir(self):
    d = QFileDialog.getExistingDirectory(self, "Choose directory", self.dir_in.text() or os.getcwd())
    if d:
        self.dir_in.setText(d)"""
previews= parse_diff_text(diff_text=diff_text)
#directory='/home/computron/Documents/pythonTools/modules/abstract_paths/src/abstract_paths/content_utils/consoles/finderConsole/tabs/editTab')
input(previews)
              
