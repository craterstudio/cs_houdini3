# This is executed on scene open
import os
import hou


if hou.hipFile.basename() == "untitled.hip":
    scene_path = "..."
else:
    scene_path = hou.hipFile.path()

print("Scene loaded: {}".format(scene_path))

try:
    from legacy_pipeline import pipeline_tools
    reload(pipeline_tools)
    scene_root = pipeline_tools.Scene_root()

    if scene_root.ver == "":
        print("Version could not be determined for this scene...")
    else:
        print("Version: {}".format(scene_root.ver))

    process_batch_mode = os.environ.get("PROCESS_BATCH_MODE", "0")
    if process_batch_mode == "0" and hou.hipFile.name() != "untitled.hip":
        if scene_root.scene_project_path != "":
            project_path = scene_root.scene_project_path
            print("Setting project path: {}".format(project_path))
            hou.hscript("setenv {} = {}".format("JOB", project_path))

    if not scene_root.project:
        print("Project could not be determined for this scene...")
    else:
        print("Project: {}".format(scene_root.project))
        print("Setting up project..")
        from cr_startup import startup_setup
        startup_setup.run(scene_root.project)

except Exception as e:
    print(e)
