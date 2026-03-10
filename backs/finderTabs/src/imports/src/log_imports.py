import logging,inspect,sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
# ─────────────────────────────────────────────────────────────
# Formatting
# ─────────────────────────────────────────────────────────────

LOG_FORMAT = (
    "[%(asctime)s] %(levelname)-8s "
    "%(caller_path)s:%(caller_line)s "
    "(%(caller_func)s) | "
    "%(message)s"
)

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class SafeFormatter(logging.Formatter):
    def format(self, record):
        record.caller_path = getattr(record, "caller_path", "<unknown>")
        record.caller_line = getattr(record, "caller_line", "?")
        record.caller_func = getattr(record, "caller_func", "<unknown>")
        return super().format(record)


# ─────────────────────────────────────────────────────────────
# Caller-injecting adapter (your logic, embedded correctly)
# ─────────────────────────────────────────────────────────────

class CallerInjectingAdapter(logging.LoggerAdapter):
    """
    Single shared logger that reports the *real runtime caller*
    using inspect.stack(), skipping logging + utility layers.
    """

    _SKIP_PREFIXES = (
        "abstract_utilities.log_utils",
        "abstract_flask.request_utils",
        "logging",
    )

    def process(self, msg, kwargs):
        caller_path = "<unknown>"
        caller_line = "?"
        caller_func = "<unknown>"

        stack = inspect.stack()
        try:
            # Skip index 0 (this process() call)
            for frame_info in stack[1:]:
                modname = frame_info.frame.f_globals.get("__name__", "")

                if modname.startswith(self._SKIP_PREFIXES):
                    continue

                caller_path = frame_info.filename
                caller_line = frame_info.lineno
                caller_func = frame_info.function
                break
        finally:
            # 🔒 critical: prevent reference cycles
            del stack

        extra = kwargs.get("extra", {})
        extra.setdefault("caller_path", caller_path)
        extra.setdefault("caller_line", caller_line)
        extra.setdefault("caller_func", caller_func)
        kwargs["extra"] = extra

        return msg, kwargs


# ─────────────────────────────────────────────────────────────
# Base logger (created once)
# ─────────────────────────────────────────────────────────────

def _build_base_logger():
    logger = logging.getLogger("app")
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    log_dir = Path.home() / ".cache" / "caller_logger_demo"
    log_dir.mkdir(parents=True, exist_ok=True)

    handler = RotatingFileHandler(
        log_dir / "app.log",
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )

    formatter = SafeFormatter(LOG_FORMAT, DATE_FORMAT)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    logger.addHandler(console)

    logger.propagate = False
    return logger


_base_logger = _build_base_logger()

# 🔥 THIS is what you import everywhere
logger = CallerInjectingAdapter(_base_logger, {})
logger.info('good to go')
