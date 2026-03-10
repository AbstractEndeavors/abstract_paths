# abstract_visibility.py
from .imports import *
def wrap_layout(layout: QLayout) -> QWidget:
    """
    Wrap any QLayout into a QWidget so it can be shown/hidden and animated.
    """
    container = QWidget()
    container.setContentsMargins(0, 0, 0, 0)     # helps stability
    container.setLayout(layout)
    return container
_QT_MAX = 16777215  # QWIDGETSIZE_MAX
class visibilityMgr(QObject):
    """
    Reusable manager for collapsible sections.
    - register() a section with a container widget or a layout (auto-wrapped)
    - auto create a QToolButton (or connect your own)
    - optional animation (height slide)
    - persists state in QSettings
    """
    toggled = QtCore.pyqtSignal(str, bool)  # name, visible
    
    def __init__(self, owner: QWidget, *,
                 settings_org="AbstractEndeavors",
                 settings_app="Visibility",
                 animate_default=False,
                 anim_duration_ms=160):
        super().__init__(owner)
        initFuncs(self)
        self._owner = owner
        self._sections = {}  # name -> dict
        self._settings = QSettings(settings_org, settings_app)
        self._animate_default = animate_default
        self._anim_ms = anim_duration_ms

    
