# This is executed on scene save
import os
import traceback

import hou


print("Scene saved: {}".format(hou.hipFile.path()))

try:
    from legacy_pipeline import pipeline_tools
    reload(pipeline_tools)
    scene_root = pipeline_tools.Scene_root()

    if scene_root.ver != "":
        print("Version: {}".format(scene_root.ver))
    else:
        print("Version could not be determined for this scene!")

except Exception as err:
    print(err.message)
    print(traceback.format_exc())
