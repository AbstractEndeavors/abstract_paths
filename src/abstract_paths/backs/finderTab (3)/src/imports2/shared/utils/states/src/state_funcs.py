from .imports import *
from .utils import *
def read_state(h) -> dict:
    try:
        return dict(
            directory=h.dir_in.text(),
            strings=h.strings_in.text(),
            allowed_exts=h.allowed_exts_in.text(),
            exclude_exts=h.exclude_exts_in.text(),
            allowed_types=h.allowed_types_in.text(),
            exclude_types=h.exclude_types_in.text(),
            allowed_dirs=h.allowed_dirs_in.text(),
            exclude_dirs=h.exclude_dirs_in.text(),
            allowed_patterns=h.allowed_patterns_in.text(),
            exclude_patterns=h.exclude_patterns_in.text(),
            add=h.chk_add.isChecked(),
            recursive=h.chk_recursive.isChecked(),
            total_strings=h.chk_total.isChecked(),
            parse_lines=h.chk_parse.isChecked(),
            get_lines=h.chk_getlines.isChecked(),
            spec_line=h.spec_spin.value(),
        )
    except Exception as e:
        logger.info(e)    
def write_state(h, s: dict):
    try:
        h._applying_remote = True
        try:
            for w, val, setter in (
                (h.dir_in,              s.get("directory",""), lambda w,v: w.setText(v)),
                (h.strings_in,          s.get("strings",""),   lambda w,v: w.setText(v)),
                (h.allowed_exts_in,     s.get("allowed_exts",""), lambda w,v: w.setText(v)),
                (h.exclude_exts_in,     s.get("exclude_exts",""), lambda w,v: w.setText(v)),

                (h.allowed_types_in,    s.get("allowed_types",""), lambda w,v: w.setText(v)),
                (h.exclude_types_in,    s.get("exclude_types",""), lambda w,v: w.setText(v)),

                (h.allowed_dirs_in,     s.get("allowed_dirs",""), lambda w,v: w.setText(v)),
                (h.exclude_dirs_in,     s.get("exclude_dirs",""), lambda w,v: w.setText(v)),

                (h.allowed_patterns_in, s.get("allowed_patterns",""), lambda w,v: w.setText(v)),
                (h.exclude_patterns_in, s.get("exclude_patterns",""), lambda w,v: w.setText(v)),
            ):
                with QSignalBlocker(w): setter(w, val)

            for w, val in (
                (h.chk_add,       s.get("add", False)),
                (h.chk_recursive, s.get("recursive", True)),
                (h.chk_total,     s.get("total_strings", False)),
                (h.chk_parse,     s.get("parse_lines", False)),
                (h.chk_getlines,  s.get("get_lines", True)),
            ):
                with QSignalBlocker(w): w.setChecked(val)

            with QSignalBlocker(h.spec_spin):
                h.spec_spin.setValue(int(s.get("spec_line", 0)) or 0)
        finally:
            h._applying_remote = False
    except Exception as e:
        logger.info(e)    
