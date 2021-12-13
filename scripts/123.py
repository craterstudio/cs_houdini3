# This is executed on houdini startup
import os
import re
import sys

import hou


COMMON_CONFIG_ROOT = os.environ["COMMON_CONFIG_ROOT"]
HOUDINI_CONFIG_ROOT = os.environ["HOUDINI_CONFIG_ROOT"]
HOUDINI_VERSION_STRING = hou.applicationVersionString()
HOUDINI_VERSION_FLOAT = float(HOUDINI_VERSION_STRING[0:4])

SHOTGUN_PIPELINE_ACTIVE = os.environ.get("SHOTGUN_PIPELINE_ACTIVE", False)


try:
    from legacy_pipeline import pipeline_tools
    reload(pipeline_tools)
    scene_root = pipeline_tools.Scene_root()
    execfile(os.path.join(COMMON_CONFIG_ROOT, "pipeline", "legacy_pipeline", "playblast_tool.py"))
except Exception as e:
    print(e)


if os.environ.get("NO_PIPELINE_HOTKEYS") == "1":
    print("Pipeline hotkey setup is disabled.")
else:
    try:
        incremental_save_symbol = "h.tool:sg_incremental_save"
        hou.hotkeys.addCommand(
            incremental_save_symbol,
            "Incremental Save",
            "Save scene incrementally (only works with shotgun pipeline enabled)"
        )
        hou.hotkeys.addAssignment(incremental_save_symbol, "alt+shift+ctrl+s")
    except Exception as e:
        print(e)
