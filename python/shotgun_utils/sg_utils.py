import sgtk
import os
import hou

try:
    import sgtk
    SGTK_LOADED = True
except ImportError:
    print("Could not load 'sgtk' module.")
    SGTK_LOADED = False


def reload_engine():
    if not SGTK_LOADED:
        msg = "WARNING: Could not load 'sgtk' module."
        hou.ui.displayMessage(msg)
        return

    current_file = hou.hipFile.path()
    if not os.path.isfile(current_file):
        msg = "WARNING: Please open a file under shotgun tracked project!"
        hou.ui.displayMessage(msg)
        return

    try:
        tk = sgtk.sgtk_from_path(current_file)
        context = tk.context_from_path(current_file)
        if not context:
            context = tk.context_empty()

        # destroying current engine if running
        if sgtk.platform.current_engine():
            sgtk.platform.current_engine().destroy()

        # starting houdini engine
        sgtk.platform.start_engine('tk-houdini', tk, context)
    except Exception as err:
        print(err.message)

# ------------------------------------------------------------------------------
# tk-houdini-arnoldnode

def convert_to_regular_arnold_nodes():
    if not SGTK_LOADED:
        msg = "WARNING: Could not load 'sgtk' module."
        hou.ui.displayMessage(msg)
        return

    engine = sgtk.platform.current_engine()
    app = engine.apps.get("tk-houdini-arnoldnode")

    if not app:
        msg = "WARNING: Toolkit application 'tk-houdini-arnoldnode' is not loaded" \
            " at the moment. Please open a scene in proper context and try again."
        hou.ui.displayMessage(msg)
    else:
        app.convert_to_regular_arnold_nodes()


def convert_back_to_tk_arnold_nodes():
    if not SGTK_LOADED:
        msg = "WARNING: Could not load 'sgtk' module."
        hou.ui.displayMessage(msg)
        return

    engine = sgtk.platform.current_engine()
    app = engine.apps.get("tk-houdini-arnoldnode")

    if not app:
        msg = "WARNING: Toolkit application 'tk-houdini-arnoldnode' is not loaded" \
            " at the moment. Please open a scene in proper context and try again."
        hou.ui.displayMessage(msg)
    else:
        app.convert_back_to_tk_arnold_nodes()

# ------------------------------------------------------------------------------
# tk-houdini-mantranode

def convert_to_regular_mantra_nodes():
    if not SGTK_LOADED:
        msg = "WARNING: Could not load 'sgtk' module."
        hou.ui.displayMessage(msg)
        return

    engine = sgtk.platform.current_engine()
    app = engine.apps.get("tk-houdini-mantranode")

    if not app:
        msg = "WARNING: Toolkit application 'tk-houdini-mantranode' is not loaded" \
            " at the moment. Please open a scene in proper context and try again."
        hou.ui.displayMessage(msg)
    else:
        app.convert_to_regular_mantra_nodes()


def convert_back_to_tk_mantra_nodes():
    if not SGTK_LOADED:
        msg = "WARNING: Could not load 'sgtk' module."
        hou.ui.displayMessage(msg)
        return

    engine = sgtk.platform.current_engine()
    app = engine.apps.get("tk-houdini-mantranode")

    if not app:
        msg = "WARNING: Toolkit application 'tk-houdini-mantranode' is not loaded" \
            " at the moment. Please open a scene in proper context and try again."
        hou.ui.displayMessage(msg)
    else:
        app.convert_back_to_tk_mantra_nodes()
