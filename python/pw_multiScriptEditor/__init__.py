import os, sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.append(CURRENT_DIR)

# HOUDINI
def showHoudini(name=None, floating=False, position=(), size=(), pane=None,
    replacePyPanel=False, hideTitleMenu=True):
    from .managers import _houdini
    reload(_houdini)
    _houdini.show(name=name, floating=floating, position=position, size=size,
        pane=pane, replacePyPanel=replacePyPanel, hideTitleMenu=hideTitleMenu)

# NUKE
def showNuke(panel=False):
    from .managers import _nuke
    reload(_nuke)
    _nuke.show(panel)


# MAYA
def showMaya(dock=False):
    from .managers import _maya
    reload(_maya)
    _maya.show(dock)

# 3DSMAX PLUS
def show3DSMax():
    sys.argv = []
    from .managers import _3dsmax
    reload(_3dsmax)
    _3dsmax.show()
